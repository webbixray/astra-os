export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthCheckResult {
  name: string;
  status: HealthStatus;
  message?: string;
  latency?: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface HealthCheck {
  name: string;
  check: () => Promise<HealthCheckResult> | HealthCheckResult;
  timeout?: number;
  critical?: boolean;
}

export class HealthChecker {
  private checks: HealthCheck[] = [];
  private results: HealthCheckResult[] = [];

  register(check: HealthCheck): void {
    this.checks.push(check);
  }

  async run(name?: string): Promise<HealthCheckResult[]> {
    const checksToRun = name
      ? this.checks.filter((c) => c.name === name)
      : this.checks;

    const results = await Promise.allSettled(
      checksToRun.map(async (check) => {
        const startTime = Date.now();
        try {
          const timeoutPromise = check.timeout
            ? new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error('Health check timed out')), check.timeout),
              )
            : null;

          const checkPromise = Promise.resolve(check.check());
          const result = timeoutPromise
            ? await Promise.race([checkPromise, timeoutPromise])
            : await checkPromise;

          return {
            ...result,
            latency: Date.now() - startTime,
            timestamp: Date.now(),
          };
        } catch (error) {
          return {
            name: check.name,
            status: 'unhealthy' as HealthStatus,
            message: (error as Error).message,
            latency: Date.now() - startTime,
            timestamp: Date.now(),
          };
        }
      }),
    );

    this.results = results.map((r) =>
      r.status === 'fulfilled' ? r.value : {
        name: 'unknown',
        status: 'unhealthy' as HealthStatus,
        message: r.reason?.message || 'Check failed',
        timestamp: Date.now(),
      },
    );

    return this.results;
  }

  getStatus(): HealthStatus {
    if (this.results.length === 0) return 'healthy';

    const hasUnhealthy = this.results.some((r) => r.status === 'unhealthy');
    const hasDegraded = this.results.some((r) => r.status === 'degraded');

    if (hasUnhealthy) return 'unhealthy';
    if (hasDegraded) return 'degraded';
    return 'healthy';
  }

  getResults(): HealthCheckResult[] {
    return [...this.results];
  }

  getLastResult(name: string): HealthCheckResult | undefined {
    return this.results.find((r) => r.name === name);
  }
}

export function createHealthCheck(check: HealthCheck): HealthCheck {
  return check;
}

export async function checkApiHealth(baseUrl: string): Promise<HealthCheckResult> {
  const startTime = Date.now();

  try {
    const response = await fetch(`${baseUrl}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });

    const data = await response.json();

    return {
      name: 'api',
      status: response.ok ? 'healthy' : 'unhealthy',
      message: data.message || `Status: ${response.status}`,
      latency: Date.now() - startTime,
      timestamp: Date.now(),
      metadata: data,
    };
  } catch (error) {
    return {
      name: 'api',
      status: 'unhealthy',
      message: (error as Error).message,
      latency: Date.now() - startTime,
      timestamp: Date.now(),
    };
  }
}

export async function checkDatabaseHealth(): Promise<HealthCheckResult> {
  const startTime = Date.now();

  try {
    const response = await fetch('/api/health/database', {
      signal: AbortSignal.timeout(5000),
    });

    return {
      name: 'database',
      status: response.ok ? 'healthy' : 'unhealthy',
      latency: Date.now() - startTime,
      timestamp: Date.now(),
    };
  } catch (error) {
    return {
      name: 'database',
      status: 'unhealthy',
      message: (error as Error).message,
      latency: Date.now() - startTime,
      timestamp: Date.now(),
    };
  }
}

export async function checkCacheHealth(): Promise<HealthCheckResult> {
  const startTime = Date.now();

  try {
    const response = await fetch('/api/health/cache', {
      signal: AbortSignal.timeout(5000),
    });

    return {
      name: 'cache',
      status: response.ok ? 'healthy' : 'unhealthy',
      latency: Date.now() - startTime,
      timestamp: Date.now(),
    };
  } catch (error) {
    return {
      name: 'cache',
      status: 'unhealthy',
      message: (error as Error).message,
      latency: Date.now() - startTime,
      timestamp: Date.now(),
    };
  }
}

export const defaultHealthChecker = new HealthChecker();
