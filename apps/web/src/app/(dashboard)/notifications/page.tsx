'use client';

import { useState } from 'react';
import {
  useNotifications, useMarkRead, useMarkAllRead, useArchiveNotification,
  useNotificationTemplates, useCreateNotificationTemplate, useDeleteNotificationTemplate,
  useNotificationPreferences, useSetNotificationPreference,
  useAnnouncements, useCreateAnnouncement, useDismissAnnouncement, useDeleteAnnouncement,
} from '@/features/notifications/api/useNotifications';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import {
  CheckCheck, Loader2, Archive, Settings, FileText, Megaphone, Inbox,
  Plus,
} from 'lucide-react';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const TABS = [
  { id: 'inbox', label: 'Inbox', icon: Inbox },
  { id: 'archive', label: 'Archive', icon: Archive },
  { id: 'preferences', label: 'Preferences', icon: Settings },
  { id: 'templates', label: 'Templates', icon: FileText },
  { id: 'announcements', label: 'Announcements', icon: Megaphone },
];

const TYPE_ICONS: Record<string, string> = {
  approval_request: '🔔', workflow_completed: '✅', workflow_failed: '❌',
  campaign_milestone: '🎯', ad_sync_completed: '🔄', content_published: '📝',
  member_joined: '👋', report_ready: '📊',
};

const TYPE_LABELS: Record<string, string> = {
  approval_request: 'Approval Required', workflow_completed: 'Workflow Completed',
  workflow_failed: 'Workflow Failed', campaign_milestone: 'Campaign Milestone',
  ad_sync_completed: 'Ad Sync Completed', content_published: 'Content Published',
  member_joined: 'Team Member Joined', report_ready: 'Report Ready',
};

const NOTIF_TYPES = [
  'general', 'campaign_milestone', 'approval_request', 'workflow_completed',
  'workflow_failed', 'ad_sync_completed', 'content_published', 'member_joined', 'report_ready',
];

const SEVERITIES = ['info', 'warning', 'error'];

export default function NotificationsPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('inbox');

  const { data: inbox, isLoading: inboxLoading } = useNotifications(orgId, false, 100, undefined, false);
  const { data: archived } = useNotifications(orgId, false, 100, undefined, true);
  const { data: templates } = useNotificationTemplates(orgId);
  const { data: prefs } = useNotificationPreferences();
  const { data: announcements } = useAnnouncements(orgId);

  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const archiveNotif = useArchiveNotification();
  const createTemplate = useCreateNotificationTemplate();
  const deleteTemplate = useDeleteNotificationTemplate();
  const setPref = useSetNotificationPreference();
  const createAnnouncement = useCreateAnnouncement();
  const dismissAnnouncement = useDismissAnnouncement();
  const deleteAnnouncement = useDeleteAnnouncement();

  const [showNewTemplate, setShowNewTemplate] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: '', type: 'general', channel: 'in_app', title_template: '', body_template: '' });
  const [showNewAnnouncement, setShowNewAnnouncement] = useState(false);
  const [annForm, setAnnForm] = useState({ title: '', body: '', severity: 'info', target_role: '' });

  function renderNotification(n: { id: string; type: string; title: string; body: string; is_read: boolean; created_at: string; channel?: string }, showArchive = true) {
    return (
      <div key={n.id} className={`flex items-start gap-4 rounded-lg border p-4 transition-colors hover:bg-accent/50 ${!n.is_read ? 'border-l-4 border-l-primary bg-accent/20' : ''}`}>
        <span className="mt-0.5 text-xl">{TYPE_ICONS[n.type] || '📬'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-medium">{n.title}</p>
              <span className="text-[11px] text-muted-foreground uppercase tracking-wide">{TYPE_LABELS[n.type] || n.type}</span>
              {n.channel && n.channel !== 'in_app' && (
                <span className="ml-2 rounded-full bg-secondary px-2 py-0.5 text-[10px]">{n.channel}</span>
              )}
            </div>
            <span className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
              {new Date(n.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          {n.body && <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{n.body}</p>}
        </div>
        <div className="flex items-center gap-1">
          {!n.is_read && (
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => markRead.mutate(n.id)}>
              Read
            </Button>
          )}
          {showArchive && (
            <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-muted-foreground" onClick={() => archiveNotif.mutate(n.id)} aria-label="Archive">
              <Archive className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-4xl px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-sm text-muted-foreground">Stay updated on workflow approvals, campaign milestones, and more.</p>
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

      {/* Inbox */}
      {tab === 'inbox' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{inbox?.filter((n) => !n.is_read).length || 0} unread</p>
            {inbox && inbox.some((n) => !n.is_read) && (
              <Button size="sm" variant="outline" onClick={() => markAllRead.mutate(orgId)} disabled={markAllRead.isPending}>
                {markAllRead.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <CheckCheck className="mr-1 h-3 w-3" />}
                Mark all read
              </Button>
            )}
          </div>
          {inboxLoading ? (
            <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
          ) : inbox && inbox.length > 0 ? (
            <div className="space-y-1">{inbox.map((n) => renderNotification(n))}</div>
          ) : (
            <div className="flex flex-col items-center py-16 text-center">
              <Inbox className="mb-4 h-12 w-12 text-muted-foreground/40" />
              <h3 className="text-lg font-medium">Inbox empty</h3>
              <p className="mt-1 text-sm text-muted-foreground">No new notifications</p>
            </div>
          )}
        </div>
      )}

      {/* Archive */}
      {tab === 'archive' && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">{archived?.length || 0} archived notifications</p>
          {archived && archived.length > 0 ? (
            <div className="space-y-1">{archived.map((n) => renderNotification(n, false))}</div>
          ) : (
            <div className="flex flex-col items-center py-16 text-center">
              <Archive className="mb-4 h-12 w-12 text-muted-foreground/40" />
              <h3 className="text-lg font-medium">No archived notifications</h3>
            </div>
          )}
        </div>
      )}

      {/* Preferences */}
      {tab === 'preferences' && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Control which notifications you receive and through which channels</p>
          <div className="rounded-lg border">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground">
              <span>Type</span>
              <span>In-App</span>
              <span>Email</span>
              <span>Slack</span>
            </div>
            {NOTIF_TYPES.map((type) => {
              return (
                <div key={type} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 border-b px-4 py-3 text-sm items-center last:border-0">
                  <span className="font-medium capitalize">{type.replace(/_/g, ' ')}</span>
                  {['in_app', 'email', 'slack'].map((ch) => {
                    const p = prefs?.find((pr) => pr.notification_type === type && pr.channel === ch);
                    const enabled = p ? p.enabled : true;
                    return (
                      <button key={ch} onClick={() => setPref.mutate({ notification_type: type, channel: ch, enabled: !enabled })}
                        className={`justify-self-start rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                          enabled ? 'bg-green-500/10 text-green-500' : 'bg-muted text-gray-400'
                        }`}>
                        {enabled ? 'On' : 'Off'}
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Templates */}
      {tab === 'templates' && (
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
      )}

      {/* Announcements */}
      {tab === 'announcements' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Broadcast announcements to your organization</p>
            <Button size="sm" onClick={() => setShowNewAnnouncement(!showNewAnnouncement)}>
              <Plus className="mr-1 h-3 w-3" />
              New Announcement
            </Button>
          </div>

          {showNewAnnouncement && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium">New Announcement</h3>
              <label htmlFor="ann-title" className="text-xs font-medium text-muted-foreground">Title</label>
              <Input id="ann-title" placeholder="Title" value={annForm.title}
                onChange={(e) => setAnnForm({ ...annForm, title: e.target.value })} />
              <label htmlFor="ann-body" className="text-xs font-medium text-muted-foreground">Body</label>
              <Textarea id="ann-body" placeholder="Body" value={annForm.body}
                onChange={(e) => setAnnForm({ ...annForm, body: e.target.value })} className="min-h-[72px]" />
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label htmlFor="ann-severity" className="text-xs font-medium text-muted-foreground">Severity</label>
                  <Select id="ann-severity" value={annForm.severity} onChange={(e) => setAnnForm({ ...annForm, severity: e.target.value })}
                    options={SEVERITIES.map((s) => ({ value: s, label: s }))} />
                </div>
                <div className="space-y-1">
                  <label htmlFor="ann-target-role" className="text-xs font-medium text-muted-foreground">Target role</label>
                  <Input id="ann-target-role" placeholder="Target role (optional)" value={annForm.target_role}
                    onChange={(e) => setAnnForm({ ...annForm, target_role: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" disabled={createAnnouncement.isPending || !annForm.title}
                  onClick={async () => {
                    await createAnnouncement.mutateAsync({ organization_id: orgId, ...annForm });
                    setShowNewAnnouncement(false);
                    setAnnForm({ title: '', body: '', severity: 'info', target_role: '' });
                  }}>
                  {createAnnouncement.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                  Publish
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowNewAnnouncement(false)}>Cancel</Button>
              </div>
            </div>
          )}

          {announcements && announcements.length > 0 ? (
            <div className="space-y-2">
              {announcements.map((a) => {
                const severityColors: Record<string, string> = {
                  info: 'border-blue-500/30 bg-blue-500/10',
                  warning: 'border-yellow-500/30 bg-yellow-500/10',
                  error: 'border-red-500/30 bg-red-500/10',
                };
                return (
                  <div key={a.id} className={`rounded-lg border p-4 ${severityColors[a.severity] || ''} ${a.expired ? 'opacity-50' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Megaphone className={`h-4 w-4 ${a.severity === 'error' ? 'text-red-500' : a.severity === 'warning' ? 'text-yellow-500' : 'text-blue-500'}`} />
                        <p className="text-sm font-medium">{a.title}</p>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                          a.severity === 'error' ? 'bg-red-500/10 text-red-500' : a.severity === 'warning' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-blue-500/10 text-blue-500'
                        }`}>{a.severity}</span>
                        {a.expired && <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-gray-500">Expired</span>}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => dismissAnnouncement.mutate(a.id)}>
                          Dismiss
                        </Button>
                        <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500"
                          onClick={() => deleteAnnouncement.mutate(a.id)} aria-label="Delete">×</Button>
                      </div>
                    </div>
                    {a.body && <p className="mt-1 text-sm text-muted-foreground">{a.body}</p>}
                    <p className="mt-1 text-[10px] text-muted-foreground">
                      {new Date(a.created_at).toLocaleDateString()}
                      {a.target_role && ` • Target: ${a.target_role}`}
                      {a.dismissed_by.length > 0 && ` • ${a.dismissed_by.length} dismissed`}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center py-16 text-center">
              <Megaphone className="mb-4 h-12 w-12 text-muted-foreground/40" />
              <h3 className="text-lg font-medium">No announcements</h3>
              <p className="mt-1 text-sm text-muted-foreground">Broadcast announcements to keep your team informed</p>
            </div>
          )}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
