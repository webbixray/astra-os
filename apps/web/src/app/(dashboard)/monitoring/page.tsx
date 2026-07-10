'use client';

import { useState } from 'react';
import { Loader2, Plus, RotateCcw, Activity, FileText, BarChart3, HeartPulse, List } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import {
  useAuditLogs, useAuditSummary,
  useJobs, useCreateJob, useRetryJob, useJobSummary,
  useUsageRecords, useUsageStats,
  useSystemHealth,
} from '@/features/monitoring/api/useMonitoring';
import { JOB_STATUS_COLORS } from '@/lib/constants';

const TABS = [
  { id: 'audit', label: 'Audit Log', icon: List },
  { id: 'jobs', label: 'Jobs', icon: FileText },
  { id: 'usage', label: 'API Usage', icon: BarChart3 },
  { id: 'health', label: 'Health', icon: HeartPulse },
];

const STATUS_COLORS = JOB_STATUS_COLORS;

export default function MonitoringPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('audit');
  const [filterAction, setFilterAction] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [jobTypeFilter, setJobTypeFilter] = useState('');

  const { data: auditLogs } = useAuditLogs(orgId, filterAction || undefined, undefined, 200);
  const { data: auditSummary } = useAuditSummary(orgId, 24);
  const { data: jobs } = useJobs(orgId, filterStatus || undefined, jobTypeFilter || undefined, 200);
  const { data: jobSummary } = useJobSummary(orgId);
  const { data: usageRecords } = useUsageRecords(orgId, 100);
  const { data: usageStats } = useUsageStats(orgId, 24);
  const { data: health } = useSystemHealth();

  const createJob = useCreateJob(orgId);
  const retryJob = useRetryJob();

  const [showCreateJob, setShowCreateJob] = useState(false);
  const [newJob, setNewJob] = useState({ job_type: '', payload: '' });

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

      {/* Audit Log */}
      {tab === 'audit' && (
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
      )}

      {/* Jobs */}
      {tab === 'jobs' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <label htmlFor="jobs-filter-status" className="sr-only">Filter by status</label>
              <Select id="jobs-filter-status" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                options={[
                  { value: '', label: 'All statuses' },
                  { value: 'queued', label: 'Queued' },
                  { value: 'running', label: 'Running' },
                  { value: 'completed', label: 'Completed' },
                  { value: 'failed', label: 'Failed' },
                ]} />
              <label htmlFor="jobs-filter-type" className="sr-only">Filter by type</label>
              <Input id="jobs-filter-type" placeholder="Filter by type..." value={jobTypeFilter}
                onChange={(e) => setJobTypeFilter(e.target.value)} className="w-40" />
              {(jobSummary as { by_status?: Record<string, number> } | undefined) && (
                <p className="text-xs text-muted-foreground">
                  {Object.entries((jobSummary as { by_status?: Record<string, number> }).by_status || {}).map(([s, c]) =>
                    `${s}: ${c}`
                  ).join(' | ')}
                </p>
              )}
            </div>
            <Button size="sm" onClick={() => setShowCreateJob(!showCreateJob)}>
              <Plus className="mr-1 h-3 w-3" />
              New Job
            </Button>
          </div>

          {showCreateJob && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium">Create Background Job</h3>
              <label htmlFor="new-job-type" className="text-xs font-medium text-muted-foreground">Job type</label>
              <Input id="new-job-type" placeholder="Job type (e.g. data_sync, report_generation)" value={newJob.job_type}
                onChange={(e) => setNewJob({ ...newJob, job_type: e.target.value })} />
              <label htmlFor="new-job-payload" className="text-xs font-medium text-muted-foreground">Payload (JSON)</label>
              <Textarea id="new-job-payload" placeholder="Payload (JSON)"
                value={newJob.payload}
                onChange={(e) => setNewJob({ ...newJob, payload: e.target.value })}
                className="font-mono" rows={3} />
              <div className="flex gap-2">
                <Button size="sm" disabled={createJob.isPending || !newJob.job_type}
                  onClick={async () => {
                    let payload = {};
                    try { payload = JSON.parse(newJob.payload || '{}'); } catch { }
                    await createJob.mutateAsync({ job_type: newJob.job_type, payload });
                    setShowCreateJob(false);
                    setNewJob({ job_type: '', payload: '' });
                  }}>
                  {createJob.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                  Create
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowCreateJob(false)}>Cancel</Button>
              </div>
            </div>
          )}

          {jobs && jobs.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground min-w-[700px]">
                <span>Type</span>
                <span>Status</span>
                <span>Retries</span>
                <span>Started</span>
                <span>Duration</span>
                <span className="col-span-2">Error / Result</span>
              </div>
              {jobs.map((j) => (
                <div key={j.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-2 border-b px-4 py-2.5 text-sm items-center last:border-0 hover:bg-accent/30 min-w-[700px]">
                  <span className="font-medium text-xs">{j.job_type}</span>
                  <span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[j.status] || ''}`}>
                      {j.status}
                    </span>
                  </span>
                  <span className="text-xs text-muted-foreground">{j.retry_count}/{j.max_retries}</span>
                  <span className="text-xs text-muted-foreground">
                    {j.started_at ? new Date(j.started_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {j.completed_at && j.started_at
                      ? `${((new Date(j.completed_at).getTime() - new Date(j.started_at).getTime()) / 1000).toFixed(1)}s`
                      : j.status === 'running' ? '...' : '—'}
                  </span>
                  <span className="col-span-2 flex items-center gap-1">
                    <span className="text-xs text-muted-foreground truncate flex-1">
                      {j.error_message || (j.result ? JSON.stringify(j.result).slice(0, 40) : '')}
                    </span>
                    {j.status === 'failed' && j.retry_count < j.max_retries && (
                      <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={() => retryJob.mutate(j.id)}>
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                    )}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-16 text-center">
              <FileText className="mb-4 h-12 w-12 text-muted-foreground/40" />
              <p className="text-lg text-muted-foreground">No jobs yet</p>
            </div>
          )}
        </div>
      )}

      {/* API Usage */}
      {tab === 'usage' && (
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
      )}

      {/* Health */}
      {tab === 'health' && (
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
      )}
    </div>
    </ErrorBoundary>
  );
}
