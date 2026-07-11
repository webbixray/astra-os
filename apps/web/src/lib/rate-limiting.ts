export interface RateLimitOptions {
  windowMs: number;
  maxRequests: number;
  keyGenerator?: (...args: unknown[]) => string;
  onLimit?: (key: string) => void;
  message?: string;
}

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

export class RateLimiter {
  private limits = new Map<string, RateLimitEntry>();
  private windowMs: number;
  private maxRequests: number;
  private message: string;

  constructor(options: RateLimitOptions) {
    this.windowMs = options.windowMs;
    this.maxRequests = options.maxRequests;
    this.message = options.message || 'Too many requests. Please try again later.';
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.limits.entries()) {
      if (now > entry.resetAt) {
        this.limits.delete(key);
      }
    }
  }

  check(key: string): { allowed: boolean; remaining: number; resetAt: number } {
    this.cleanup();

    const now = Date.now();
    const entry = this.limits.get(key);

    if (!entry || now > entry.resetAt) {
      this.limits.set(key, {
        count: 1,
        resetAt: now + this.windowMs,
      });
      return {
        allowed: true,
        remaining: this.maxRequests - 1,
        resetAt: now + this.windowMs,
      };
    }

    if (entry.count >= this.maxRequests) {
      return {
        allowed: false,
        remaining: 0,
        resetAt: entry.resetAt,
      };
    }

    entry.count++;
    return {
      allowed: true,
      remaining: this.maxRequests - entry.count,
      resetAt: entry.resetAt,
    };
  }

  async acquire(key: string): Promise<void> {
    const { allowed, resetAt } = this.check(key);

    if (!allowed) {
      const waitTime = resetAt - Date.now();
      await new Promise((resolve) => setTimeout(resolve, waitTime));

      const retryResult = this.check(key);
      if (!retryResult.allowed) {
        throw new Error(this.message);
      }
    }
  }

  reset(key?: string): void {
    if (key) {
      this.limits.delete(key);
    } else {
      this.limits.clear();
    }
  }

  getRemaining(key: string): number {
    const entry = this.limits.get(key);
    if (!entry || Date.now() > entry.resetAt) {
      return this.maxRequests;
    }
    return Math.max(0, this.maxRequests - entry.count);
  }
}

export function createRateLimiter(options: RateLimitOptions): RateLimiter {
  return new RateLimiter(options);
}

export const apiRateLimiter = createRateLimiter({
  windowMs: 60 * 1000,
  maxRequests: 100,
  message: 'API rate limit exceeded. Please wait before making more requests.',
});

export const authRateLimiter = createRateLimiter({
  windowMs: 15 * 60 * 1000,
  maxRequests: 5,
  message: 'Too many authentication attempts. Please try again later.',
});

export const uploadRateLimiter = createRateLimiter({
  windowMs: 60 * 1000,
  maxRequests: 10,
  message: 'Upload limit exceeded. Please wait before uploading more files.',
});

export async function rateLimitedFetch(
  url: string,
  options?: RequestInit,
  rateLimiter?: RateLimiter,
): Promise<Response> {
  const limiter = rateLimiter || apiRateLimiter;
  const key = `fetch:${url}`;

  await limiter.acquire(key);

  return fetch(url, options);
}
