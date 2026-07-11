export interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  timestamp: number;
  userId?: string;
  sessionId?: string;
  tags?: Record<string, string>;
  level: 'error' | 'warning' | 'info';
  fingerprint?: string;
}

export interface ErrorReporter {
  report(error: Error | ErrorReport, extras?: Record<string, unknown>): void;
  setContext(key: string, value: string | number | boolean): void;
  setUser(user: { id: string; email?: string; name?: string }): void;
  addBreadcrumb(breadcrumb: Breadcrumb): void;
}

export interface Breadcrumb {
  category: string;
  message: string;
  level: 'error' | 'warning' | 'info' | 'debug';
  timestamp: number;
  data?: Record<string, unknown>;
}

function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function generateFingerprint(error: Error): string {
  const stack = error.stack || '';
  const message = error.message;
  return btoa(`${message}:${stack.split('\n').slice(0, 3).join('|')}`);
}

class LocalErrorReporter implements ErrorReporter {
  private errors: ErrorReport[] = [];
  private breadcrumbs: Breadcrumb[] = [];
  private context: Record<string, string | number | boolean> = {};
  private user?: { id: string; email?: string; name?: string };
  private maxErrors = 100;
  private maxBreadcrumbs = 50;

  report(error: Error | ErrorReport, extras?: Record<string, unknown>): void {
    const report: ErrorReport = 'id' in error
      ? error
      : {
          id: generateId(),
          message: error.message,
          stack: error.stack,
          url: typeof window !== 'undefined' ? window.location.href : '',
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
          timestamp: Date.now(),
          level: 'error',
          fingerprint: generateFingerprint(error),
          ...extras,
        };

    this.errors.push(report);
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(-this.maxErrors / 2);
    }

    console.error('[ErrorReporter]', report.message, report);

    if (typeof window !== 'undefined' && navigator.sendBeacon) {
      try {
        navigator.sendBeacon('/api/errors', JSON.stringify(report));
      } catch {
        // Silently fail
      }
    }
  }

  setContext(key: string, value: string | number | boolean): void {
    this.context[key] = value;
  }

  setUser(user: { id: string; email?: string; name?: string }): void {
    this.user = user;
  }

  addBreadcrumb(breadcrumb: Breadcrumb): void {
    this.breadcrumbs.push(breadcrumb);
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.maxBreadcrumbs / 2);
    }
  }

  getErrors(): ErrorReport[] {
    return [...this.errors];
  }

  getBreadcrumbs(): Breadcrumb[] {
    return [...this.breadcrumbs];
  }

  clear(): void {
    this.errors = [];
    this.breadcrumbs = [];
  }
}

export const errorReporter: ErrorReporter = new LocalErrorReporter();

export function captureException(error: Error, extras?: Record<string, unknown>): void {
  errorReporter.report(error, extras);
}

export function captureMessage(message: string, level: 'error' | 'warning' | 'info' = 'info'): void {
  errorReporter.report({
    id: generateId(),
    message,
    url: typeof window !== 'undefined' ? window.location.href : '',
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    timestamp: Date.now(),
    level,
  });
}

export function addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>): void {
  errorReporter.addBreadcrumb({
    ...breadcrumb,
    timestamp: Date.now(),
  });
}

export function withErrorTracking<T extends (...args: unknown[]) => unknown>(
  fn: T,
  name?: string,
): T {
  return ((...args: unknown[]) => {
    try {
      addBreadcrumb({
        category: 'function',
        message: `Calling ${name || fn.name || 'anonymous'}`,
        level: 'info',
      });
      return fn(...args);
    } catch (error) {
      captureException(error as Error, { function: name || fn.name, args: JSON.stringify(args) });
      throw error;
    }
  }) as T;
}

export async function withAsyncErrorTracking<T>(
  fn: () => Promise<T>,
  name?: string,
): Promise<T> {
  try {
    addBreadcrumb({
      category: 'async',
      message: `Calling ${name || 'async function'}`,
      level: 'info',
    });
    return await fn();
  } catch (error) {
    captureException(error as Error, { function: name });
    throw error;
  }
}
