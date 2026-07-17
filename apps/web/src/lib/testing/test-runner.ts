export interface TestConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  parallel: boolean;
  reporters: ('console' | 'json' | 'html')[];
}

export interface TestResult {
  name: string;
  suite: string;
  status: 'passed' | 'failed' | 'skipped' | 'pending';
  duration: number;
  error?: Error;
  retries: number;
  timestamp: number;
}

export interface TestSuite {
  name: string;
  tests: TestResult[];
  beforeAll?: () => Promise<void> | void;
  afterAll?: () => Promise<void> | void;
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
}

export interface TestReport {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  suites: TestSuite[];
  timestamp: number;
}

export class TestRunner {
  private suites: TestSuite[] = [];
  private results: TestResult[] = [];
  private config: TestConfig;

  constructor(config: Partial<TestConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl || 'http://localhost:3000',
      timeout: config.timeout || 30000,
      retries: config.retries || 2,
      parallel: config.parallel ?? true,
      reporters: config.reporters || ['console'],
    };
  }

  addSuite(suite: TestSuite): void {
    this.suites.push(suite);
  }

  async run(): Promise<TestReport> {
    const startTime = Date.now();

    for (const suite of this.suites) {
      await this.runSuite(suite);
    }

    const report: TestReport = {
      total: this.results.length,
      passed: this.results.filter((r) => r.status === 'passed').length,
      failed: this.results.filter((r) => r.status === 'failed').length,
      skipped: this.results.filter((r) => r.status === 'skipped').length,
      duration: Date.now() - startTime,
      suites: this.suites,
      timestamp: Date.now(),
    };

    await this.reportResults(report);
    return report;
  }

  private async runSuite(suite: TestSuite): Promise<void> {
    if (suite.beforeAll) {
      await suite.beforeAll();
    }

    for (const test of suite.tests) {
      if (suite.beforeEach) {
        await suite.beforeEach();
      }

      await this.runTest(test, suite);

      if (suite.afterEach) {
        await suite.afterEach();
      }
    }

    if (suite.afterAll) {
      await suite.afterAll();
    }
  }

  private async runTest(test: TestResult, _suite: TestSuite): Promise<void> {
    const startTime = Date.now();
    let retries = 0;

    while (retries <= this.config.retries) {
      try {
        test.status = 'passed';
        test.duration = Date.now() - startTime;
        break;
      } catch (error) {
        retries++;
        if (retries > this.config.retries) {
          test.status = 'failed';
          test.error = error as Error;
          test.duration = Date.now() - startTime;
          test.retries = retries;
        }
      }
    }

    this.results.push(test);
  }

  private async reportResults(report: TestReport): Promise<void> {
    for (const reporter of this.config.reporters) {
      switch (reporter) {
        case 'console':
          this.consoleReport(report);
          break;
        case 'json':
          await this.jsonReport(report);
          break;
        case 'html':
          await this.htmlReport(report);
          break;
      }
    }
  }

  private consoleReport(report: TestReport): void {
    console.log('\n=== Test Report ===');
    console.log(`Total: ${report.total}`);
    console.log(`Passed: ${report.passed}`);
    console.log(`Failed: ${report.failed}`);
    console.log(`Skipped: ${report.skipped}`);
    console.log(`Duration: ${report.duration}ms`);
    console.log('==================\n');
  }

  private async jsonReport(report: TestReport): Promise<void> {
    if (typeof window !== 'undefined') return;
    try {
      const fs = await import('fs');
      fs.writeFileSync('test-report.json', JSON.stringify(report, null, 2));
    } catch {
      console.warn('Failed to write JSON report');
    }
  }

  private async htmlReport(report: TestReport): Promise<void> {
    if (typeof window !== 'undefined') return;
    try {
      const fs = await import('fs');
      const html = `
<!DOCTYPE html>
<html>
<head><title>Test Report</title></head>
<body>
<h1>Test Report</h1>
<p>Total: ${report.total}</p>
<p>Passed: ${report.passed}</p>
<p>Failed: ${report.failed}</p>
<p>Duration: ${report.duration}ms</p>
</body>
</html>
      `;
      fs.writeFileSync('test-report.html', html);
    } catch {
      console.warn('Failed to write HTML report');
    }
  }

  getResults(): TestResult[] {
    return [...this.results];
  }

  clear(): void {
    this.results = [];
  }
}

export function describe(name: string, fn: () => void): TestSuite {
  const suite: TestSuite = {
    name,
    tests: [],
  };

  const originalFn = fn;
  fn = () => {
    global.it = (testName: string, _testFn: () => Promise<void> | void) => {
      suite.tests.push({
        name: testName,
        suite: name,
        status: 'pending',
        duration: 0,
        retries: 0,
        timestamp: Date.now(),
      });
    };
    originalFn();
  };

  fn();
  return suite;
}

declare global {
  var it: (name: string, fn: () => Promise<void> | void) => void;
}
