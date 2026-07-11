'use client';

import { useState } from 'react';
import { useNotificationTemplates, useCreateNotificationTemplate, useDeleteNotificationTemplate } from '@/features/notifications/api/useNotifications';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Loader2, FileText, Plus } from 'lucide-react';

const NOTIF_TYPES = [
  'general', 'campaign_milestone', 'approval_request', 'workflow_completed',
  'workflow_failed', 'ad_sync_completed', 'content_published', 'member_joined', 'report_ready',
];

export function NotificationsTemplatesTab({ orgId }: { orgId: string }) {
  const { data: templates } = useNotificationTemplates(orgId);
  const createTemplate = useCreateNotificationTemplate();
  const deleteTemplate = useDeleteNotificationTemplate();

  const [showNewTemplate, setShowNewTemplate] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: '', type: 'general', channel: 'in_app', title_template: '', body_template: '' });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Reusable notification templates with variable substitution</p>
        <Button size="sm" onClick={() => setShowNewTemplate(!showNewTemplate)}>
          <Plus className="mr-1 h-3 w-3" />
          New Template
        </Button>
      </div>

      {showNewTemplate && (
        <div className="rounded-lg border bg-card p-4 space-y-3">
          <h3 className="text-sm font-medium">New Notification Template</h3>
          <label htmlFor="template-name" className="text-xs font-medium text-muted-foreground">Name</label>
          <Input id="template-name" placeholder="Name" value={templateForm.name}
            onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label htmlFor="template-type" className="text-xs font-medium text-muted-foreground">Type</label>
              <Select id="template-type" value={templateForm.type}
                onChange={(e) => setTemplateForm({ ...templateForm, type: e.target.value })}
                options={NOTIF_TYPES.map((t) => ({ value: t, label: t.replace(/_/g, ' ') }))} />
            </div>
            <div className="space-y-1">
              <label htmlFor="template-channel" className="text-xs font-medium text-muted-foreground">Channel</label>
              <Select id="template-channel" value={templateForm.channel}
                onChange={(e) => setTemplateForm({ ...templateForm, channel: e.target.value })}
                options={[
                  { value: 'in_app', label: 'In-App' },
                  { value: 'email', label: 'Email' },
                  { value: 'slack', label: 'Slack' },
                ]} />
            </div>
          </div>
          <label htmlFor="template-title" className="text-xs font-medium text-muted-foreground">Title template</label>
          <Input id="template-title" placeholder="Title template (e.g. Campaign {{name}} completed)" value={templateForm.title_template}
            onChange={(e) => setTemplateForm({ ...templateForm, title_template: e.target.value })} />
          <label htmlFor="template-body" className="text-xs font-medium text-muted-foreground">Body template</label>
          <Textarea id="template-body" placeholder="Body template (optional)" value={templateForm.body_template}
            onChange={(e) => setTemplateForm({ ...templateForm, body_template: e.target.value })} className="min-h-[60px]" />
          <div className="flex gap-2">
            <Button size="sm" disabled={createTemplate.isPending || !templateForm.name}
              onClick={async () => {
                await createTemplate.mutateAsync({ organization_id: orgId, ...templateForm });
                setShowNewTemplate(false);
                setTemplateForm({ name: '', type: 'general', channel: 'in_app', title_template: '', body_template: '' });
              }}>
              {createTemplate.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              Save Template
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowNewTemplate(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {templates && templates.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {templates.map((t) => (
            <div key={t.id} className="rounded-lg border bg-card p-4 space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-sm">{t.name}</p>
                  <div className="flex gap-1 mt-1">
                    <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px]">{t.type}</span>
                    <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px]">{t.channel}</span>
                  </div>
                </div>
                <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500"
                  onClick={() => deleteTemplate.mutate(t.id)} aria-label="Delete">×</Button>
              </div>
              <p className="text-xs text-muted-foreground">{t.title_template}</p>
              {t.variables.length > 0 && (
                <p className="text-[10px] text-muted-foreground">Variables: {t.variables.join(', ')}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <FileText className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <h3 className="text-lg font-medium">No templates yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">Create notification templates for reusable messaging</p>
        </div>
      )}
    </div>
  );
}
