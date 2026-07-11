'use client';

import { lazy, Suspense, useState } from 'react';
import { List, FileText, BarChart3, HeartPulse, Loader2 } from 'lucide-react';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const MonitoringAuditTab = lazy(() =>
  import('./MonitoringAuditTab').then((m) => ({ default: m.MonitoringAuditTab }))
);
const MonitoringJobsTab = lazy(() =>
  import('./MonitoringJobsTab').then((m) => ({ default: m.MonitoringJobsTab }))
);
const MonitoringUsageTab = lazy(() =>
  import('./MonitoringUsageTab').then((m) => ({ default: m.MonitoringUsageTab }))
);
const MonitoringHealthTab = lazy(() =>
  import('./MonitoringHealthTab').then((m) => ({ default: m.MonitoringHealthTab }))
);

const TABS = [
  { id: 'audit', label: 'Audit Log', icon: List },
  { id: 'jobs', label: 'Jobs', icon: FileText },
  { id: 'usage', label: 'API Usage', icon: BarChart3 },
  { id: 'health', label: 'Health', icon: HeartPulse },
];

function TabFallback() {
  return (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

export default function MonitoringPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('audit');
  const [filterAction, setFilterAction] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [jobTypeFilter, setJobTypeFilter] = useState('');

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">System Monitoring</h1>
          <p className="text-sm text-muted-foreground">Audit logs, job tracking, API usage, and health checks</p>
        </div>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === t.id ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}>
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      <Suspense fallback={<TabFallback />}>
        {tab === 'audit' && (
          <MonitoringAuditTab orgId={orgId} filterAction={filterAction} setFilterAction={setFilterAction} />
        )}
        {tab === 'jobs' && (
          <MonitoringJobsTab
            orgId={orgId}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            jobTypeFilter={jobTypeFilter}
            setJobTypeFilter={setJobTypeFilter}
          />
        )}
        {tab === 'usage' && (
          <MonitoringUsageTab orgId={orgId} />
        )}
        {tab === 'health' && (
          <MonitoringHealthTab />
        )}
      </Suspense>
    </div>
    </ErrorBoundary>
  );
}
