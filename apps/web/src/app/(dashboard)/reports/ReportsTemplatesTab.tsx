'use client';

import { useState } from 'react';
import { Plus, Trash2, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import {
  useReportTemplates, useCreateReportTemplate, useDeleteReportTemplate,
  getReportExportUrl,
} from '@/features/reports/api/useReports';

const REPORT_TYPES = [
  { value: 'overview', label: 'Overview' },
  { value: 'campaigns', label: 'Campaigns' },
  { value: 'ads', label: 'Ad Performance' },
  { value: 'content', label: 'Content' },
  { value: 'email', label: 'Email' },
  { value: 'platform_comparison', label: 'Platform Comparison' },
];

export function ReportsTemplatesTab({ orgId }: { orgId: string }) {
  const { data: templates } = useReportTemplates(orgId);
  const createTemplate = useCreateReportTemplate();
  const deleteTemplate = useDeleteReportTemplate();

  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateType, setTemplateType] = useState('overview');

  const handleCreateTemplate = () => {
    if (!templateName.trim()) return;
    createTemplate.mutate(
      { orgId, name: templateName.trim(), report_type: templateType },
      { onSuccess: () => { setShowCreateTemplate(false); setTemplateName(''); } },
    );
  };

  return (
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
  );
}
