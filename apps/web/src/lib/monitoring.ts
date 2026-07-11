export interface PerformanceMetric {
  name: string;
  value: number;
  unit: 'ms' | 'bytes' | 'count' | 'percent';
  timestamp: number;
  tags?: Record<string, string>;
}

export interface PerformanceEntry {
  startTime: number;
  endTime: number;
  duration: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private marks: Map<string, number> = new Map();
  private observers: Map<string, PerformanceObserver> = new Map();

  mark(name: string): void {
    this.marks.set(name, performance.now());
  }

  measure(name: string, startMark: string, endMark?: string): number {
    const startTime = this.marks.get(startMark);
    if (startTime === undefined) {
      throw new Error(`Mark "${startMark}" not found`);
    }

    const endTime = endMark ? this.marks.get(endMark) : performance.now();
    if (endTime === undefined) {
      throw new Error(`Mark "${endMark}" not found`);
    }

    const duration = endTime - startTime;
    this.record({
      name,
      value: duration,
      unit: 'ms',
      timestamp: Date.now(),
    });

    return duration;
  }

  record(metric: PerformanceMetric): void {
    this.metrics.push(metric);
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-500);
    }
  }

  timer(name: string): { stop: () => number } {
    const startTime = performance.now();
    return {
      stop: () => {
        const duration = performance.now() - startTime;
        this.record({
          name,
          value: duration,
          unit: 'ms',
          timestamp: Date.now(),
        });
        return duration;
      },
    };
  }

  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const timer = this.timer(name);
    try {
      return await fn();
    } finally {
      timer.stop();
    }
  }

  observeLongTasks(): void {
    if (typeof PerformanceObserver === 'undefined') return;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.record({
            name: 'long-task',
            value: entry.duration,
            unit: 'ms',
            timestamp: Date.now(),
            tags: { entryType: entry.entryType },
          });
        }
      });
      observer.observe({ entryTypes: ['longtask'] });
      this.observers.set('longtask', observer);
    } catch {
      console.warn('Long task observer not supported');
    }
  }

  observeLCP(): void {
    if (typeof PerformanceObserver === 'undefined') return;

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        if (lastEntry) {
          this.record({
            name: 'lcp',
            value: lastEntry.startTime,
            unit: 'ms',
            timestamp: Date.now(),
          });
        }
      });
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.set('lcp', observer);
    } catch {
      console.warn('LCP observer not supported');
    }
  }

  observeFID(): void {
    if (typeof PerformanceObserver === 'undefined') return;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.record({
            name: 'fid',
            value: (entry as PerformanceEventTiming).processingStart - entry.startTime,
            unit: 'ms',
            timestamp: Date.now(),
          });
        }
      });
      observer.observe({ entryTypes: ['first-input'] });
      this.observers.set('fid', observer);
    } catch {
      console.warn('FID observer not supported');
    }
  }

  observeCLS(): void {
    if (typeof PerformanceObserver === 'undefined') return;

    let clsValue = 0;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as LayoutShift).hadRecentInput) {
            clsValue += (entry as LayoutShift).value;
            this.record({
              name: 'cls',
              value: clsValue,
              unit: 'percent',
              timestamp: Date.now(),
            });
          }
        }
      });
      observer.observe({ entryTypes: ['layout-shift'] });
      this.observers.set('cls', observer);
    } catch {
      console.warn('CLS observer not supported');
    }
  }

  getMetrics(name?: string): PerformanceMetric[] {
    if (name) {
      return this.metrics.filter((m) => m.name === name);
    }
    return [...this.metrics];
  }

  getAverage(name: string): number | null {
    const metrics = this.getMetrics(name);
    if (metrics.length === 0) return null;
    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  getPercentile(name: string, percentile: number): number | null {
    const metrics = this.getMetrics(name).sort((a, b) => a.value - b.value);
    if (metrics.length === 0) return null;
    const index = Math.ceil((percentile / 100) * metrics.length) - 1;
    return metrics[index]?.value ?? null;
  }

  clear(): void {
    this.metrics = [];
    this.marks.clear();
  }

  disconnect(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }
}

export const performanceMonitor = new PerformanceMonitor();

export function measureRender<T>(name: string, fn: () => T): T {
  const timer = performanceMonitor.timer(`render:${name}`);
  try {
    return fn();
  } finally {
    timer.stop();
  }
}

export function measureEffect(name: string, fn: () => void | (() => void)): void | (() => void) {
  const timer = performanceMonitor.timer(`effect:${name}`);
  const cleanup = fn();
  timer.stop();
  return cleanup;
}
