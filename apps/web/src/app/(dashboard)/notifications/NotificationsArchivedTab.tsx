'use client';

import { useNotifications, useMarkRead } from '@/features/notifications/api/useNotifications';
import { Button } from '@/components/ui/button';
import { Archive } from 'lucide-react';

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

export function NotificationsArchivedTab({ orgId }: { orgId: string }) {
  const { data: archived } = useNotifications(orgId, false, 100, undefined, true);
  const markRead = useMarkRead();

  function renderNotification(n: { id: string; type: string; title: string; body: string; is_read: boolean; created_at: string; channel?: string }) {
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
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{archived?.length || 0} archived notifications</p>
      {archived && archived.length > 0 ? (
        <div className="space-y-1">{archived.map((n) => renderNotification(n))}</div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Archive className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <h3 className="text-lg font-medium">No archived notifications</h3>
        </div>
      )}
    </div>
  );
}
