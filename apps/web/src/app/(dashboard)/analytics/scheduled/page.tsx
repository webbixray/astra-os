'use client';

import { useState } from 'react';
import {
  Calendar,
  Plus,
  Trash2,
  Clock,
  Mail,
  FileText,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  useReportSchedules,
  useCreateReportSchedule,
  useDeleteReportSchedule,
} from '@/features/reports/api/useReports';
import { useOrg } from '@/lib/org';
import Link from 'next/link';
import { SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const FREQ_LABELS: Record<string, string> = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
};

const TYPE_LABELS: Record<string, string> = {
  overview: 'Overview',
  campaigns: 'Campaigns',
  ads: 'Ad Performance',
};

export default function ScheduledReportsPage() {
  const { orgId } = useOrg();
  const { data: schedules, isLoading } = useReportSchedules(orgId);
  const createMutation = useCreateReportSchedule();
  const deleteMutation = useDeleteReportSchedule();

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '',
    report_type: 'overview',
    frequency: 'weekly',
    recipients: '',
  });

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      organization_id: orgId,
      name: form.name,
      report_type: form.report_type,
      frequency: form.frequency,
      recipients: form.recipients
        .split(',')
        .map((e: string) => e.trim())
        .filter(Boolean),
    });
    setShowCreate(false);
    setForm({ name: '', report_type: 'overview', frequency: 'weekly', recipients: '' });
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/analytics">
            <Button variant="ghost" size="icon" aria-label="Back">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <Calendar className="h-6 w-6" />
            <div>
              <h1 className="text-2xl font-semibold">Scheduled Reports</h1>
              <p className="text-sm text-muted-foreground">
                Automated report delivery
              </p>
            </div>
          </div>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" />
          New Schedule
        </Button>
      </div>

      {showCreate && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-col gap-4">
            <div>
              <label htmlFor="sched-name" className="text-xs font-medium text-muted-foreground">Report name</label>
              <Input
                id="sched-name"
                placeholder="Report Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="sched-type" className="text-xs font-medium text-muted-foreground">Report type</label>
              <Select
                id="sched-type"
                value={form.report_type}
                onChange={(e) => setForm({ ...form, report_type: e.target.value })}
                options={[
                  { value: 'overview', label: 'Overview' },
                  { value: 'campaigns', label: 'Campaigns' },
                  { value: 'ads', label: 'Ad Performance' },
                ]}
              />
            </div>
            <div>
              <label htmlFor="sched-freq" className="text-xs font-medium text-muted-foreground">Frequency</label>
              <Select
                id="sched-freq"
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                options={[
                  { value: 'daily', label: 'Daily' },
                  { value: 'weekly', label: 'Weekly' },
                  { value: 'monthly', label: 'Monthly' },
                ]}
              />
            </div>
            <div>
              <label htmlFor="sched-recipients" className="text-xs font-medium text-muted-foreground">Recipients</label>
              <Input
                id="sched-recipients"
                placeholder="Recipients (comma-separated emails)"
                value={form.recipients}
                onChange={(e) => setForm({ ...form, recipients: e.target.value })}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!form.name || createMutation.isPending}>
                Create
              </Button>
              <Button variant="ghost" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : schedules && schedules.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {schedules.map((s) => (
            <div key={s.id} className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <h3 className="font-medium">{s.name}</h3>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    s.is_active
                      ? 'bg-green-500/10 text-green-500'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {s.is_active ? 'Active' : 'Paused'}
                </span>
              </div>
              <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                <p className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  {TYPE_LABELS[s.report_type] || s.report_type}
                </p>
                <p className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {FREQ_LABELS[s.frequency] || s.frequency}
                </p>
                {s.recipients.length > 0 && (
                  <p className="flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    {s.recipients.join(', ')}
                  </p>
                )}
                {s.last_run_at && (
                  <p className="pt-1 text-xs">Last: {s.last_run_at.split('T')[0]}</p>
                )}
              </div>
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-500 hover:text-red-600"
                  aria-label="Delete"
                  onClick={() => deleteMutation.mutate(s.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Calendar className="h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">No scheduled reports</p>
          <p className="text-sm text-muted-foreground">
            Schedule automated report delivery to your inbox
          </p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Schedule Report
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
