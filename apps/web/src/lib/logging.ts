export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  context?: Record<string, unknown>;
  error?: Error;
}

class Logger {
  private level: LogLevel = 'info';
  private context: Record<string, unknown> = {};
  private entries: LogEntry[] = [];
  private maxEntries = 500;

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  setContext(context: Record<string, unknown>): void {
    this.context = { ...this.context, ...context };
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>, error?: Error): void {
    if (!this.shouldLog(level)) return;

    const entry: LogEntry = {
      level,
      message,
      timestamp: Date.now(),
      context: { ...this.context, ...context },
      error,
    };

    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries / 2);
    }

    const prefix = `[${new Date(entry.timestamp).toISOString()}] [${level.toUpperCase()}]`;
    const consoleContext = Object.keys(entry.context || {}).length > 0 ? entry.context : '';

    switch (level) {
      case 'debug':
        console.debug(prefix, message, consoleContext);
        break;
      case 'info':
        console.info(prefix, message, consoleContext);
        break;
      case 'warn':
        console.warn(prefix, message, consoleContext);
        break;
      case 'error':
        console.error(prefix, message, consoleContext, error);
        break;
    }
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context);
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context);
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context);
  }

  error(message: string, error?: Error, context?: Record<string, unknown>): void {
    this.log('error', message, context, error);
  }

  child(context: Record<string, unknown>): Logger {
    const childLogger = new Logger();
    childLogger.level = this.level;
    childLogger.context = { ...this.context, ...context };
    return childLogger;
  }

  getEntries(level?: LogLevel): LogEntry[] {
    if (level) {
      return this.entries.filter((e) => e.level === level);
    }
    return [...this.entries];
  }

  clear(): void {
    this.entries = [];
  }

  flush(): void {
    if (this.entries.length > 0 && typeof navigator !== 'undefined' && navigator.sendBeacon) {
      navigator.sendBeacon('/api/logs', JSON.stringify(this.entries));
      this.entries = [];
    }
  }
}

export const logger = new Logger();

export function createLogger(name: string): Logger {
  return logger.child({ logger: name });
}

export function logApiRequest(method: string, url: string, status?: number, duration?: number): void {
  logger.info(`${method} ${url}`, {
    method,
    url,
    status,
    duration: duration ? `${duration.toFixed(0)}ms` : undefined,
  });
}

export function logUserAction(action: string, details?: Record<string, unknown>): void {
  logger.info(`User action: ${action}`, { action, ...details });
}

export function logPerformance(name: string, value: number, unit = 'ms'): void {
  logger.info(`Performance: ${name}`, { name, value, unit });
}
