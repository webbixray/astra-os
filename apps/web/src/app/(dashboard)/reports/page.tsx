'use client';

import { lazy, Suspense, useState } from 'react';
import { BarChart3, FileText, Calendar, Download, Mail, Layers, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const ReportsTemplatesTab = lazy(() => import('./ReportsTemplatesTab').then(m => ({ default: m.ReportsTemplatesTab })));
const ReportsSchedulesTab = lazy(() => import('./ReportsSchedulesTab').then(m => ({ default: m.ReportsSchedulesTab })));
const ReportsExportTab = lazy(() => import('./ReportsExportTab').then(m => ({ default: m.ReportsExportTab })));
const ReportsDeliverTab = lazy(() => import('./ReportsDeliverTab').then(m => ({ default: m.ReportsDeliverTab })));
const ReportsCompareTab = lazy(() => import('./ReportsCompareTab').then(m => ({ default: m.ReportsCompareTab })));
const ReportsLogsTab = lazy(() => import('./ReportsLogsTab').then(m => ({ default: m.ReportsLogsTab })));

function TabSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-6 w-48 rounded bg-muted" />
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="h-4 w-32 rounded bg-muted" />
        <div className="h-4 w-64 rounded bg-muted" />
        <div className="h-4 w-48 rounded bg-muted" />
      </div>
    </div>
  );
}

const tabs = [
  { key: 'templates', label: 'Templates', icon: FileText },
  { key: 'schedules', label: 'Schedules', icon: Calendar },
  { key: 'export', label: 'Export', icon: Download },
  { key: 'deliver', label: 'Deliver', icon: Mail },
  { key: 'compare', label: 'Compare', icon: Layers },
  { key: 'logs', label: 'History', icon: Clock },
];

export default function ReportsPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('templates');

  return (
    <ErrorBoundary>
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-5 w-5" />
          <h1 className="text-lg font-semibold">Reports</h1>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Tabs */}
        <div className="hidden md:block w-40 shrink-0 border-r p-3 space-y-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors',
                tab === t.key
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
              )}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <Suspense fallback={<TabSkeleton />}>
            {tab === 'templates' && <ReportsTemplatesTab orgId={orgId} />}
            {tab === 'schedules' && <ReportsSchedulesTab orgId={orgId} />}
            {tab === 'export' && <ReportsExportTab orgId={orgId} />}
            {tab === 'deliver' && <ReportsDeliverTab orgId={orgId} />}
            {tab === 'compare' && <ReportsCompareTab orgId={orgId} />}
            {tab === 'logs' && <ReportsLogsTab orgId={orgId} />}
          </Suspense>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
