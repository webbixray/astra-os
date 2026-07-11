export interface PerformanceTestConfig {
  iterations: number;
  warmupIterations: number;
  timeout: number;
}

export interface PerformanceTestResult {
  name: string;
  average: number;
  median: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
  iterations: number;
  operationsPerSecond: number;
}

export class PerformanceTester {
  private results: PerformanceTestResult[] = [];
  private config: PerformanceTestConfig;

  constructor(config: Partial<PerformanceTestConfig> = {}) {
    this.config = {
      iterations: config.iterations || 100,
      warmupIterations: config.warmupIterations || 10,
      timeout: config.timeout || 30000,
    };
  }

  async test(name: string, fn: () => Promise<void> | void): Promise<PerformanceTestResult> {
    const timings: number[] = [];

    for (let i = 0; i < this.config.warmupIterations; i++) {
      await fn();
    }

    for (let i = 0; i < this.config.iterations; i++) {
      const start = performance.now();
      await fn();
      timings.push(performance.now() - start);
    }

    timings.sort((a, b) => a - b);

    const result: PerformanceTestResult = {
      name,
      average: timings.reduce((a, b) => a + b, 0) / timings.length,
      median: timings[Math.floor(timings.length / 2)],
      p95: timings[Math.floor(timings.length * 0.95)],
      p99: timings[Math.floor(timings.length * 0.99)],
      min: timings[0],
      max: timings[timings.length - 1],
      iterations: this.config.iterations,
      operationsPerSecond: 1000 / (timings.reduce((a, b) => a + b, 0) / timings.length),
    };

    this.results.push(result);
    return result;
  }

  async testSync(name: string, fn: () => void): Promise<PerformanceTestResult> {
    return this.test(name, fn);
  }

  getResults(): PerformanceTestResult[] {
    return [...this.results];
  }

  clear(): void {
    this.results = [];
  }

  compare(result1: PerformanceTestResult, result2: PerformanceTestResult): {
    faster: string;
    improvement: number;
  } {
    if (result1.average < result2.average) {
      return {
        faster: result1.name,
        improvement: ((result2.average - result1.average) / result2.average) * 100,
      };
    }
    return {
      faster: result2.name,
      improvement: ((result1.average - result2.average) / result1.average) * 100,
    };
  }
}

export async function benchmark<T>(
  name: string,
  fn: () => T | Promise<T>,
  iterations: number = 100,
): Promise<{ name: string; averageMs: number; opsPerSec: number }> {
  const timings: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await fn();
    timings.push(performance.now() - start);
  }

  const average = timings.reduce((a, b) => a + b, 0) / timings.length;

  return {
    name,
    averageMs: average,
    opsPerSec: 1000 / average,
  };
}

export function measureMemory<T>(fn: () => T): { result: T; memoryDelta: number } {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return { result: fn(), memoryDelta: 0 };
  }

  const memory = (performance as { memory: { usedJSHeapSize: number } }).memory;
  const before = memory.usedJSHeapSize;
  const result = fn();
  const after = memory.usedJSHeapSize;

  return {
    result,
    memoryDelta: after - before,
  };
}

export async function measureAsyncMemory<T>(fn: () => Promise<T>): Promise<{ result: T; memoryDelta: number }> {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return { result: await fn(), memoryDelta: 0 };
  }

  const memory = (performance as { memory: { usedJSHeapSize: number } }).memory;
  const before = memory.usedJSHeapSize;
  const result = await fn();
  const after = memory.usedJSHeapSize;

  return {
    result,
    memoryDelta: after - before,
  };
}

export function reportPerformance(results: PerformanceTestResult[]): void {
  console.log('\n=== Performance Report ===');
  results.forEach((result) => {
    console.log(`\n${result.name}:`);
    console.log(`  Average: ${result.average.toFixed(2)}ms`);
    console.log(`  Median: ${result.median.toFixed(2)}ms`);
    console.log(`  P95: ${result.p95.toFixed(2)}ms`);
    console.log(`  P99: ${result.p99.toFixed(2)}ms`);
    console.log(`  Min: ${result.min.toFixed(2)}ms`);
    console.log(`  Max: ${result.max.toFixed(2)}ms`);
    console.log(`  Ops/sec: ${result.operationsPerSecond.toFixed(2)}`);
  });
}
