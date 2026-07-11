'use client';

import { BarChart3 } from 'lucide-react';
import { useUsageRecords, useUsageStats } from '@/features/monitoring/api/useMonitoring';

interface MonitoringUsageTabProps {
  orgId: string;
}

export function MonitoringUsageTab({ orgId }: MonitoringUsageTabProps) {
  const { data: usageRecords } = useUsageRecords(orgId, 100);
  const { data: usageStats } = useUsageStats(orgId, 24);

  return (
    <div className="space-y-4">
      {usageStats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div className="rounded-lg border bg-card p-4">
            <p className="text-xs text-muted-foreground">API Calls (24h)</p>
            <p className="mt-1 text-2xl font-semibold">{usageStats.total_calls.toLocaleString()}</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-xs text-muted-foreground">Avg Response Time</p>
            <p className="mt-1 text-2xl font-semibold">{usageStats.avg_response_time_ms}ms</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-xs text-muted-foreground">Max Response Time</p>
            <p className="mt-1 text-2xl font-semibold">{usageStats.max_response_time_ms}ms</p>
          </div>
        </div>
      )}

      {usageStats && usageStats.by_endpoint && usageStats.by_endpoint.length > 0 && (
        <div className="rounded-lg border">
          <div className="border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground">
            Endpoint Breakdown
          </div>
          {usageStats.by_endpoint.map((ep, i) => (
            <div key={i} className="grid grid-cols-2 sm:grid-cols-4 gap-2 border-b px-4 py-2.5 text-sm items-center last:border-0">
              <span className="font-mono text-xs">{ep.method}</span>
              <span className="text-xs text-muted-foreground col-span-2">{ep.endpoint}</span>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium">{ep.count} calls</span>
                <span className="text-xs text-muted-foreground">{ep.avg_response_time_ms}ms avg</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {usageRecords && usageRecords.length > 0 && (
        <div className="overflow-x-auto rounded-lg border">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground min-w-[500px]">
            <span>Time</span>
            <span>Method</span>
            <span className="col-span-2">Endpoint</span>
            <span>Status / Time</span>
          </div>
          {usageRecords.slice(0, 50).map((r) => (
            <div key={r.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 border-b px-4 py-2 text-sm items-center last:border-0 min-w-[500px]">
              <span className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
              <span className="font-mono text-xs">{r.method}</span>
              <span className="col-span-2 text-xs text-muted-foreground truncate">{r.endpoint}</span>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${r.status_code >= 400 ? 'text-red-500' : 'text-green-600'}`}>
                  {r.status_code}
                </span>
                <span className="text-xs text-muted-foreground">{r.response_time_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {(!usageRecords || usageRecords.length === 0) && (
        <div className="flex flex-col items-center py-16 text-center">
          <BarChart3 className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No usage records yet</p>
        </div>
      )}
    </div>
  );
}
