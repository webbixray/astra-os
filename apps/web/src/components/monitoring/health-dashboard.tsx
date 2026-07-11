'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  checks: Record<string, boolean>;
  details: Record<string, string>;
  duration_ms: string;
}

interface MetricData {
  label: string;
  value: string | number;
  status: 'ok' | 'warning' | 'error';
  icon?: string;
}

export function MonitoringDashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const data = await api.get<HealthStatus>('/health');
      setHealth(data);
      setError('');
    } catch {
      setError('Failed to fetch health status');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4">
        <p className="text-sm text-destructive">{error}</p>
        <button onClick={fetchHealth} className="mt-2 text-sm underline hover:no-underline">
          Retry
        </button>
      </div>
    );
  }

  if (!health) return null;

  const metrics: MetricData[] = [
    {
      label: 'API Status',
      value: health.status === 'ok' ? 'Healthy' : 'Degraded',
      status: health.status === 'ok' ? 'ok' : 'warning',
      icon: health.status === 'ok' ? '\u2713' : '\u26A0',
    },
    {
      label: 'Version',
      value: health.version,
      status: 'ok',
    },
    {
      label: 'Response Time',
      value: `${health.duration_ms}ms`,
      status: parseFloat(health.duration_ms) < 100 ? 'ok' : 'warning',
    },
    {
      label: 'Database',
      value: health.checks.database ? 'Connected' : 'Error',
      status: health.checks.database ? 'ok' : 'error',
    },
    {
      label: 'Redis',
      value: health.checks.redis ? 'Connected' : health.details.redis || 'Not Configured',
      status: health.checks.redis ? 'ok' : health.details.redis === 'not_configured' ? 'ok' : 'error',
    },
    {
      label: 'Temporal',
      value: health.checks.temporal ? 'Connected' : health.details.temporal || 'Not Configured',
      status: health.checks.temporal ? 'ok' : health.details.temporal === 'not_configured' ? 'ok' : 'error',
    },
  ];

  const statusColors = {
    ok: 'text-green-600 bg-green-50 dark:bg-green-950',
    warning: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950',
    error: 'text-red-600 bg-red-50 dark:bg-red-950',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">System Health</h2>
        <button
          onClick={fetchHealth}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="rounded-lg border bg-card p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{metric.label}</span>
              <span
                className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${statusColors[metric.status]}`}
              >
                {metric.icon && <span className="mr-1">{metric.icon}</span>}
                {metric.value}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border bg-card p-4">
        <h3 className="mb-4 text-sm font-medium">Service Details</h3>
        <div className="space-y-2">
          {Object.entries(health.details).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground capitalize">{key}</span>
              <span className="font-mono">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="text-xs text-muted-foreground">
        Last checked: {new Date(health.timestamp).toLocaleString()}
      </div>
    </div>
  );
}
