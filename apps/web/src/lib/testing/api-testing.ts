export interface ApiTestConfig {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout?: number;
}

export interface ApiTestResult {
  method: string;
  url: string;
  status: number;
  duration: number;
  passed: boolean;
  error?: string;
}

export class ApiTestClient {
  private config: ApiTestConfig;
  private results: ApiTestResult[] = [];

  constructor(config: ApiTestConfig) {
    this.config = {
      timeout: 10000,
      ...config,
    };
  }

  async get(url: string, options?: RequestInit): Promise<Response> {
    return this.request('GET', url, options);
  }

  async post(url: string, body?: unknown, options?: RequestInit): Promise<Response> {
    return this.request('POST', url, {
      ...options,
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  }

  async put(url: string, body?: unknown, options?: RequestInit): Promise<Response> {
    return this.request('PUT', url, {
      ...options,
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  }

  async patch(url: string, body?: unknown, options?: RequestInit): Promise<Response> {
    return this.request('PATCH', url, {
      ...options,
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  }

  async delete(url: string, options?: RequestInit): Promise<Response> {
    return this.request('DELETE', url, options);
  }

  async request(method: string, url: string, options?: RequestInit): Promise<Response> {
    const startTime = Date.now();
    const fullUrl = `${this.config.baseUrl}${url}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(fullUrl, {
        ...options,
        method,
        signal: controller.signal,
        headers: {
          ...this.config.headers,
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      this.results.push({
        method,
        url,
        status: response.status,
        duration: Date.now() - startTime,
        passed: response.ok,
      });

      return response;
    } catch (error) {
      this.results.push({
        method,
        url,
        status: 0,
        duration: Date.now() - startTime,
        passed: false,
        error: (error as Error).message,
      });
      throw error;
    }
  }

  getResults(): ApiTestResult[] {
    return [...this.results];
  }

  clear(): void {
    this.results = [];
  }
}

export interface ApiTestCase {
  name: string;
  method: string;
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  expectedStatus: number;
  expectedBody?: (body: unknown) => boolean;
}

export async function runApiTests(
  config: ApiTestConfig,
  testCases: ApiTestCase[],
): Promise<{ passed: number; failed: number; results: ApiTestResult[] }> {
  const client = new ApiTestClient(config);
  let passed = 0;
  let failed = 0;

  for (const testCase of testCases) {
    try {
      const response = await client.request(testCase.method, testCase.url, {
        body: testCase.body ? JSON.stringify(testCase.body) : undefined,
        headers: {
          'Content-Type': 'application/json',
          ...testCase.headers,
        },
      });

      if (response.status === testCase.expectedStatus) {
        if (testCase.expectedBody) {
          const body = await response.json();
          if (testCase.expectedBody(body)) {
            passed++;
            console.log(`✓ ${testCase.name}`);
          } else {
            failed++;
            console.log(`✗ ${testCase.name} - Body validation failed`);
          }
        } else {
          passed++;
          console.log(`✓ ${testCase.name}`);
        }
      } else {
        failed++;
        console.log(`✗ ${testCase.name} - Expected ${testCase.expectedStatus}, got ${response.status}`);
      }
    } catch (error) {
      failed++;
      console.log(`✗ ${testCase.name} - ${(error as Error).message}`);
    }
  }

  return {
    passed,
    failed,
    results: client.getResults(),
  };
}

export function expect(response: Response) {
  return {
    toHaveStatus(status: number): boolean {
      if (response.status !== status) {
        console.error(`Expected status ${status}, got ${response.status}`);
        return false;
      }
      return true;
    },
    async toHaveBody(expected: unknown): Promise<boolean> {
      const body = await response.json();
      if (JSON.stringify(body) !== JSON.stringify(expected)) {
        console.error('Body mismatch');
        return false;
      }
      return true;
    },
    async toHaveProperty(property: string): Promise<boolean> {
      const body = await response.json();
      if (!(property in body)) {
        console.error(`Body missing property: ${property}`);
        return false;
      }
      return true;
    },
  };
}
