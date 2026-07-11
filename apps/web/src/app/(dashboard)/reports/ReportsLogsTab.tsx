'use client';

import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDeliveryLogs } from '@/features/reports/api/useReports';
import { REPORT_STATUS_COLORS } from '@/lib/constants';

const STATUS_COLORS = REPORT_STATUS_COLORS;

export function ReportsLogsTab({ orgId }: { orgId: string }) {
  const { data: deliveryLogs } = useDeliveryLogs(orgId);

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="font-semibold">Delivery History</h2>
      <div className="rounded-lg border bg-card">
        {deliveryLogs && deliveryLogs.length > 0 ? (
          <div className="divide-y">
            {deliveryLogs.map((log) => (
              <div key={log.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div className="flex items-center gap-3">
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    STATUS_COLORS[log.status] || 'bg-muted text-muted-foreground',
                  )}>
                    {log.status === 'delivered' ? <CheckCircle2 className="inline h-3 w-3 mr-1" /> :
                     log.status === 'failed' ? <XCircle className="inline h-3 w-3 mr-1" /> :
                     <RefreshCw className="inline h-3 w-3 mr-1" />}
                    {log.status}
                  </span>
                  <span className="capitalize">{log.report_type}</span>
                  <span className="text-xs text-muted-foreground">{log.format}</span>
                  <span className="text-xs text-muted-foreground">{log.channel}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(log.generated_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="p-6 text-center text-sm text-muted-foreground">No delivery history yet</p>
        )}
      </div>
    </div>
  );
}
