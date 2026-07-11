'use client';

import { List } from 'lucide-react';
import { Select } from '@/components/ui/select';
import { useAuditLogs, useAuditSummary } from '@/features/monitoring/api/useMonitoring';

interface MonitoringAuditTabProps {
  orgId: string;
  filterAction: string;
  setFilterAction: (value: string) => void;
}

export function MonitoringAuditTab({ orgId, filterAction, setFilterAction }: MonitoringAuditTabProps) {
  const { data: auditLogs } = useAuditLogs(orgId, filterAction || undefined, undefined, 200);
  const { data: auditSummary } = useAuditSummary(orgId, 24);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <label htmlFor="audit-filter-action" className="sr-only">Filter by action</label>
          <Select id="audit-filter-action" value={filterAction} onChange={(e) => setFilterAction(e.target.value)}
            options={[
              { value: '', label: 'All actions' },
              { value: 'create', label: 'Create' },
              { value: 'update', label: 'Update' },
              { value: 'delete', label: 'Delete' },
              { value: 'login', label: 'Login' },
              { value: 'logout', label: 'Logout' },
              { value: 'config_change', label: 'Config Change' },
              { value: 'export', label: 'Export' },
            ]} />
        </div>
        {(auditSummary as { total: number; period_hours: number } | undefined) && (
          <p className="text-xs text-muted-foreground">
            {(auditSummary as { total: number; period_hours: number }).total} actions in last {(auditSummary as { total: number; period_hours: number }).period_hours}h
          </p>
        )}
      </div>

      {auditLogs && auditLogs.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground min-w-[600px]">
            <span>Time</span>
            <span>Action</span>
            <span>Resource</span>
            <span className="col-span-2">Details</span>
            <span>IP</span>
          </div>
          {auditLogs.map((e) => (
            <div key={e.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 border-b px-4 py-2.5 text-sm items-center last:border-0 hover:bg-accent/30 min-w-[600px]">
              <span className="text-xs text-muted-foreground">
                {new Date(e.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium w-fit ${
                e.action === 'create' ? 'bg-green-500/10 text-green-500' :
                e.action === 'delete' ? 'bg-red-500/10 text-red-500' :
                e.action === 'update' ? 'bg-blue-500/10 text-blue-500' :
                'bg-muted text-muted-foreground'
              }`}>{e.action}</span>
              <span className="text-xs text-muted-foreground">{e.resource_type}
                {e.resource_id && <span className="ml-1 opacity-50">/{e.resource_id.slice(0, 8)}</span>}
              </span>
              <span className="col-span-2 text-xs text-muted-foreground truncate">
                {JSON.stringify(e.details).slice(0, 80)}
              </span>
              <span className="text-xs text-muted-foreground">{e.ip_address || '—'}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <List className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No audit logs yet</p>
        </div>
      )}
    </div>
  );
}
