export interface RetryOptions {
  maxRetries?: number;
  delay?: number;
  backoff?: 'linear' | 'exponential';
  maxDelay?: number;
  retryCondition?: (error: Error) => boolean;
  onRetry?: (error: Error, attempt: number) => void;
}

export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {},
): Promise<T> {
  const {
    maxRetries = 3,
    delay = 1000,
    backoff = 'exponential',
    maxDelay = 30000,
    retryCondition = () => true,
    onRetry,
  } = options;

  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries && retryCondition(lastError)) {
        onRetry?.(lastError, attempt + 1);
        const waitTime = Math.min(
          backoff === 'exponential'
            ? delay * Math.pow(2, attempt)
            : delay * (attempt + 1),
          maxDelay,
        );
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }
  }

  throw lastError;
}

export interface CircuitBreakerOptions {
  threshold?: number;
  resetTimeout?: number;
  monitorInterval?: number;
}

export type CircuitState = 'closed' | 'open' | 'half-open';

export class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount = 0;
  private lastFailureTime = 0;
  private successCount = 0;
  private threshold: number;
  private resetTimeout: number;

  constructor(options: CircuitBreakerOptions = {}) {
    this.threshold = options.threshold ?? 5;
    this.resetTimeout = options.resetTimeout ?? 60000;
  }

  getState(): CircuitState {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime >= this.resetTimeout) {
        this.state = 'half-open';
        this.successCount = 0;
      }
    }
    return this.state;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    const currentState = this.getState();

    if (currentState === 'open') {
      throw new Error('Circuit breaker is open');
    }

    try {
      const result = await fn();

      if (currentState === 'half-open') {
        this.successCount++;
        if (this.successCount >= 3) {
          this.reset();
        }
      }

      this.failureCount = 0;
      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();

      if (this.failureCount >= this.threshold) {
        this.state = 'open';
      }

      throw error;
    }
  }

  reset(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.successCount = 0;
  }

  isAvailable(): boolean {
    return this.getState() !== 'open';
  }

  getFailureCount(): number {
    return this.failureCount;
  }
}

export interface TimeoutOptions {
  timeout: number;
  message?: string;
}

export async function withTimeout<T>(
  fn: () => Promise<T>,
  options: TimeoutOptions,
): Promise<T> {
  const { timeout, message = 'Operation timed out' } = options;

  return Promise.race([
    fn(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(message)), timeout),
    ),
  ]);
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let inThrottle = false;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

export function memoize<T extends (...args: unknown[]) => unknown>(
  fn: T,
  options: { ttl?: number; maxSize?: number } = {},
): T {
  const cache = new Map<string, { value: ReturnType<T>; timestamp: number }>();
  const { ttl = 60000, maxSize = 100 } = options;

  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);

    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.value;
    }

    const value = fn(...args) as ReturnType<T>;

    if (cache.size >= maxSize) {
      const firstKey = cache.keys().next().value;
      if (firstKey) cache.delete(firstKey);
    }

    cache.set(key, { value, timestamp: Date.now() });
    return value;
  }) as T;
}
