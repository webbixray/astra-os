'use client';

import { useState } from 'react';
import { useAnnouncements, useCreateAnnouncement, useDismissAnnouncement, useDeleteAnnouncement } from '@/features/notifications/api/useNotifications';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Loader2, Megaphone, Plus } from 'lucide-react';

const SEVERITIES = ['info', 'warning', 'error'];

export function NotificationsAnnouncementsTab({ orgId }: { orgId: string }) {
  const { data: announcements } = useAnnouncements(orgId);
  const createAnnouncement = useCreateAnnouncement();
  const dismissAnnouncement = useDismissAnnouncement();
  const deleteAnnouncement = useDeleteAnnouncement();

  const [showNewAnnouncement, setShowNewAnnouncement] = useState(false);
  const [annForm, setAnnForm] = useState({ title: '', body: '', severity: 'info', target_role: '' });

  return (
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
  );
}
