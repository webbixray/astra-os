'use client';

import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import {
  useReportSchedules, useCreateReportSchedule, useDeleteReportSchedule,
} from '@/features/reports/api/useReports';

const REPORT_TYPES = [
  { value: 'overview', label: 'Overview' },
  { value: 'campaigns', label: 'Campaigns' },
  { value: 'ads', label: 'Ad Performance' },
  { value: 'content', label: 'Content' },
  { value: 'email', label: 'Email' },
  { value: 'platform_comparison', label: 'Platform Comparison' },
];

const FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Bi-Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
];

export function ReportsSchedulesTab({ orgId }: { orgId: string }) {
  const { data: schedules } = useReportSchedules(orgId);
  const createSchedule = useCreateReportSchedule();
  const deleteSchedule = useDeleteReportSchedule();

  const [showCreateSchedule, setShowCreateSchedule] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleType, setScheduleType] = useState('overview');
  const [scheduleFreq, setScheduleFreq] = useState('weekly');
  const [scheduleRecipients, setScheduleRecipients] = useState('');
  const [scheduleActive, setScheduleActive] = useState(true);

  const handleCreateSchedule = () => {
    if (!scheduleName.trim()) return;
    createSchedule.mutate({
      organization_id: orgId,
      name: scheduleName.trim(),
      report_type: scheduleType,
      frequency: scheduleFreq,
      is_active: scheduleActive,
      recipients: scheduleRecipients.split(',').map((r) => r.trim()).filter(Boolean),
    }, {
      onSuccess: () => { setShowCreateSchedule(false); setScheduleName(''); setScheduleRecipients(''); },
    });
  };

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Scheduled Reports</h2>
        <Button size="sm" onClick={() => setShowCreateSchedule(true)}>
          <Plus className="mr-1 h-3.5 w-3.5" /> New Schedule
        </Button>
      </div>

      {showCreateSchedule && (
        <div className="rounded-lg border bg-card p-4 space-y-3">
          <label htmlFor="schedule-name" className="text-xs font-medium text-muted-foreground">Schedule name</label>
          <Input id="schedule-name" placeholder="Schedule name" value={scheduleName}
            onChange={(e) => setScheduleName(e.target.value)} />
          <label htmlFor="schedule-type" className="text-xs font-medium text-muted-foreground">Report type</label>
          <Select id="schedule-type" value={scheduleType} onChange={(e) => setScheduleType(e.target.value)}
            options={REPORT_TYPES} />
          <label htmlFor="schedule-freq" className="text-xs font-medium text-muted-foreground">Frequency</label>
          <Select id="schedule-freq" value={scheduleFreq} onChange={(e) => setScheduleFreq(e.target.value)}
            options={FREQUENCIES} />
          <label className="flex items-center gap-2 text-sm">
            <Input type="checkbox" checked={scheduleActive}
              onChange={(e) => setScheduleActive(e.target.checked)} className="w-4" />
            Active
          </label>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreateSchedule} disabled={!scheduleName.trim()}>Create</Button>
            <Button size="sm" variant="ghost" onClick={() => setShowCreateSchedule(false)}>Cancel</Button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {schedules?.map((s) => (
          <div key={s.id} className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
            <div className="flex items-center gap-3">
              <span className={cn('h-2 w-2 rounded-full', s.is_active ? 'bg-green-500' : 'bg-muted')} />
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-muted-foreground">
                  {s.report_type} · {s.frequency}
                  {s.next_run_at && ` · Next: ${new Date(s.next_run_at).toLocaleDateString()}`}
                </p>
              </div>
            </div>
            <button onClick={() => deleteSchedule.mutate(s.id)}
              className="text-muted-foreground hover:text-red-500" aria-label="Delete">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
        {(!schedules || schedules.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-8">No schedules yet</p>
        )}
      </div>
    </div>
  );
}
