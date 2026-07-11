'use client';

import { Loader2, Activity } from 'lucide-react';
import { useSystemHealth } from '@/features/monitoring/api/useMonitoring';

export function MonitoringHealthTab() {
  const { data: health } = useSystemHealth();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">System health and service status</p>
        {health && (
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${
            health.status === 'healthy' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
          }`}>
            {health.status}
          </span>
        )}
      </div>

      {health ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(health.checks).map(([name, check]) => (
            <div key={name} className="rounded-lg border bg-card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium text-sm capitalize">{name}</span>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  check.status === 'healthy' ? 'bg-green-500/10 text-green-500' :
                  check.status === 'degraded' ? 'bg-yellow-500/10 text-yellow-500' :
                  'bg-red-500/10 text-red-500'
                }`}>{check.status}</span>
              </div>
              {check.response_time_ms !== undefined && (
                <p className="text-xs text-muted-foreground">
                  Response: {check.response_time_ms}ms
                </p>
              )}
              {check.error && (
                <p className="text-xs text-red-500">{check.error}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      <div className="rounded-lg border bg-card p-4">
        <p className="text-xs text-muted-foreground">
          Last checked: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : '—'}
        </p>
      </div>
    </div>
  );
}
