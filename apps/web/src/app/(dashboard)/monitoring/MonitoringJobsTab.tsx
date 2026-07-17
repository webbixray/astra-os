'use client';

import { useState } from 'react';
import { Loader2, Plus, RotateCcw, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useJobs, useCreateJob, useRetryJob, useJobSummary } from '@/features/monitoring/api/useMonitoring';
import { JOB_STATUS_COLORS } from '@/lib/constants';

const STATUS_COLORS = JOB_STATUS_COLORS;

interface MonitoringJobsTabProps {
  orgId: string;
  filterStatus: string;
  setFilterStatus: (value: string) => void;
  jobTypeFilter: string;
  setJobTypeFilter: (value: string) => void;
}

export function MonitoringJobsTab({
  orgId,
  filterStatus,
  setFilterStatus,
  jobTypeFilter,
  setJobTypeFilter,
}: MonitoringJobsTabProps) {
  const { data: jobs } = useJobs(orgId, filterStatus || undefined, jobTypeFilter || undefined, 200);
  const { data: jobSummary } = useJobSummary(orgId);
  const createJob = useCreateJob(orgId);
  const retryJob = useRetryJob();

  const [showCreateJob, setShowCreateJob] = useState(false);
  const [newJob, setNewJob] = useState({ job_type: '', payload: '' });

  return (
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
                try { payload = JSON.parse(newJob.payload || '{}'); } catch { /* noop */ }
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
  );
}
