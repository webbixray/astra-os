'use client';

import { useNotificationPreferences, useSetNotificationPreference } from '@/features/notifications/api/useNotifications';

const NOTIF_TYPES = [
  'general', 'campaign_milestone', 'approval_request', 'workflow_completed',
  'workflow_failed', 'ad_sync_completed', 'content_published', 'member_joined', 'report_ready',
];

export function NotificationsPreferencesTab() {
  const { data: prefs } = useNotificationPreferences();
  const setPref = useSetNotificationPreference();

  return (
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
  );
}
