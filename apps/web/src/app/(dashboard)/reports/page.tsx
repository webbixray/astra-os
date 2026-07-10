'use client';

import { useState } from 'react';
import {
  FileText, Plus, Trash2, Download, Calendar,
  BarChart3, Layers, Mail, Clock,
  CheckCircle2, XCircle, RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import {
  useReportTemplates, useCreateReportTemplate, useDeleteReportTemplate,
  useReportSchedules, useCreateReportSchedule, useDeleteReportSchedule,
  useDeliveryLogs, useDeliverReport, useComparePeriods,
  getReportExportUrl,
} from '@/features/reports/api/useReports';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { REPORT_STATUS_COLORS } from '@/lib/constants';

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

const FORMATS = ['csv', 'json', 'html'];
const CHANNELS = ['download', 'email', 'slack', 'webhook'];

const STATUS_COLORS = REPORT_STATUS_COLORS;

export default function ReportsPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('templates');

  const { data: templates } = useReportTemplates(orgId);
  const { data: schedules } = useReportSchedules(orgId);
  const { data: deliveryLogs } = useDeliveryLogs(orgId);
  const createTemplate = useCreateReportTemplate();
  const deleteTemplate = useDeleteReportTemplate();
  const createSchedule = useCreateReportSchedule();
  const deleteSchedule = useDeleteReportSchedule();
  const deliverReport = useDeliverReport();
  const comparePeriods = useComparePeriods();

  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateType, setTemplateType] = useState('overview');

  const [showCreateSchedule, setShowCreateSchedule] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleType, setScheduleType] = useState('overview');
  const [scheduleFreq, setScheduleFreq] = useState('weekly');
  const [scheduleRecipients, setScheduleRecipients] = useState('');
  const [scheduleActive, setScheduleActive] = useState(true);

  const [deliverChannel, setDeliverChannel] = useState('email');
  const [deliverRecipient, setDeliverRecipient] = useState('');
  const [deliverFormat, setDeliverFormat] = useState('csv');
  const [deliverType, setDeliverType] = useState('overview');
  const [deliverDays, setDeliverDays] = useState(30);
  const [delivering, setDelivering] = useState(false);

  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const [selectedExportType, setSelectedExportType] = useState('overview');
  const [selectedFormat, setSelectedFormat] = useState('csv');
  const [exportDays, setExportDays] = useState(30);

  const tabs = [
    { key: 'templates', label: 'Templates', icon: FileText },
    { key: 'schedules', label: 'Schedules', icon: Calendar },
    { key: 'export', label: 'Export', icon: Download },
    { key: 'deliver', label: 'Deliver', icon: Mail },
    { key: 'compare', label: 'Compare', icon: Layers },
    { key: 'logs', label: 'History', icon: Clock },
  ];

  const handleCreateTemplate = () => {
    if (!templateName.trim()) return;
    createTemplate.mutate(
      { orgId, name: templateName.trim(), report_type: templateType },
      { onSuccess: () => { setShowCreateTemplate(false); setTemplateName(''); } },
    );
  };

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

  const handleDeliver = () => {
    setDelivering(true);
    deliverReport.mutate({
      orgId, report_type: deliverType, channel: deliverChannel,
      recipient: deliverRecipient, format: deliverFormat, days: deliverDays,
    }, {
      onSettled: () => setDelivering(false),
      onSuccess: () => { setDeliverRecipient(''); },
    });
  };

  const handleCompare = async () => {
    setCompareLoading(true);
    comparePeriods.mutate({ orgId }, {
      onSuccess: (data) => setCompareResult(data as unknown as Record<string, unknown>),
      onSettled: () => setCompareLoading(false),
    });
  };

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
          {tab === 'templates' && (
            <div className="max-w-2xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Report Templates</h2>
                <Button size="sm" onClick={() => setShowCreateTemplate(true)}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> New Template
                </Button>
              </div>

              {showCreateTemplate && (
                <div className="rounded-lg border bg-card p-4 space-y-3">
                  <label htmlFor="report-template-name" className="text-xs font-medium text-muted-foreground">Template name</label>
                  <Input id="report-template-name" placeholder="Template name" value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)} />
                  <label htmlFor="report-template-type" className="text-xs font-medium text-muted-foreground">Report type</label>
                  <Select id="report-template-type" value={templateType} onChange={(e) => setTemplateType(e.target.value)}
                    options={REPORT_TYPES} />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleCreateTemplate} disabled={!templateName.trim()}>Create</Button>
                    <Button size="sm" variant="ghost" onClick={() => setShowCreateTemplate(false)}>Cancel</Button>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                {templates?.map((t) => (
                  <div key={t.id} className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
                    <div>
                      <p className="text-sm font-medium">{t.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{t.report_type}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <a href={getReportExportUrl(orgId, t.report_type, 'csv', 30)}
                        className="text-xs text-muted-foreground hover:text-foreground" target="_blank" rel="noreferrer noopener" aria-label="Download CSV">
                        <Download className="h-3.5 w-3.5" />
                      </a>
                      <button onClick={() => deleteTemplate.mutate(t.id)}
                        className="text-muted-foreground hover:text-red-500" aria-label="Delete">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
                {(!templates || templates.length === 0) && (
                  <p className="text-sm text-muted-foreground text-center py-8">No templates yet</p>
                )}
              </div>
            </div>
          )}

          {tab === 'schedules' && (
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
          )}

          {tab === 'export' && (
            <div className="max-w-xl space-y-4">
              <h2 className="font-semibold">Export Report</h2>
              <div className="rounded-lg border bg-card p-4 space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Report Type</label>
                  <Select value={selectedExportType} onChange={(e) => setSelectedExportType(e.target.value)}
                    options={REPORT_TYPES} />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Format</label>
                  <div className="mt-1 flex gap-2">
                    {FORMATS.map((f) => (
                      <button key={f} onClick={() => setSelectedFormat(f)}
                        className={cn(
                          'rounded border px-3 py-1.5 text-sm transition-colors',
                          selectedFormat === f ? 'border-primary bg-primary/10 font-medium' : 'hover:bg-accent',
                        )}>
                        {f.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Days</label>
                  <Input type="number" value={exportDays} onChange={(e) => setExportDays(Number(e.target.value))}
                    min={1} max={365} className="w-24" />
                </div>
                <a
                  href={getReportExportUrl(orgId, selectedExportType, selectedFormat, exportDays)}
                  target="_blank" rel="noreferrer noopener"
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                  <Download className="h-4 w-4" />
                  Export {selectedFormat.toUpperCase()}
                </a>
              </div>
            </div>
          )}

          {tab === 'deliver' && (
            <div className="max-w-xl space-y-4">
              <h2 className="font-semibold">Deliver Report</h2>
              <div className="rounded-lg border bg-card p-4 space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Report Type</label>
                  <Select value={deliverType} onChange={(e) => setDeliverType(e.target.value)}
                    options={REPORT_TYPES} />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Channel</label>
                  <Select value={deliverChannel} onChange={(e) => setDeliverChannel(e.target.value)}
                    options={CHANNELS.map((c) => ({ value: c, label: c }))} />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Recipient (email/@channel/URL)</label>
                  <Input value={deliverRecipient}
                    onChange={(e) => setDeliverRecipient(e.target.value)}
                    placeholder="user@example.com" />
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs font-medium text-muted-foreground">Format</label>
                    <Select value={deliverFormat} onChange={(e) => setDeliverFormat(e.target.value)}
                      options={FORMATS.map((f) => ({ value: f, label: f.toUpperCase() }))} />
                  </div>
                  <div className="w-24">
                    <label className="text-xs font-medium text-muted-foreground">Days</label>
                    <Input type="number" value={deliverDays}
                      onChange={(e) => setDeliverDays(Number(e.target.value))} min={1} max={365} />
                  </div>
                </div>
                <Button onClick={handleDeliver} disabled={delivering || !deliverRecipient.trim()}>
                  {delivering ? 'Sending...' : 'Send Report'}
                </Button>
              </div>
            </div>
          )}

          {tab === 'compare' && (
            <div className="max-w-2xl space-y-4">
              <h2 className="font-semibold">Period Comparison</h2>
              <div className="rounded-lg border bg-card p-4 space-y-4">
                <p className="text-sm text-muted-foreground">
                  Compare current 30-day performance against the previous period.
                </p>
                <Button onClick={handleCompare} disabled={compareLoading}>
                  {compareLoading ? 'Comparing...' : 'Compare Periods'}
                </Button>
              </div>

              {compareResult && (
                <div className="rounded-lg border bg-card p-4">
                  <h3 className="text-sm font-medium mb-3">Comparison Results</h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(compareResult).filter(([k]) => k !== 'comparison').map(([key, val]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                        <span>{String(val)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'logs' && (
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
          )}
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
