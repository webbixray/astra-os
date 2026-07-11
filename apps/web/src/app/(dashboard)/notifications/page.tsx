'use client';

import { lazy, Suspense, useState } from 'react';
import { Loader2, Archive, Settings, FileText, Megaphone, Inbox } from 'lucide-react';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const NotificationsInboxTab = lazy(() => import('./NotificationsInboxTab').then((m) => ({ default: m.NotificationsInboxTab })));
const NotificationsArchivedTab = lazy(() => import('./NotificationsArchivedTab').then((m) => ({ default: m.NotificationsArchivedTab })));
const NotificationsPreferencesTab = lazy(() => import('./NotificationsPreferencesTab').then((m) => ({ default: m.NotificationsPreferencesTab })));
const NotificationsTemplatesTab = lazy(() => import('./NotificationsTemplatesTab').then((m) => ({ default: m.NotificationsTemplatesTab })));
const NotificationsAnnouncementsTab = lazy(() => import('./NotificationsAnnouncementsTab').then((m) => ({ default: m.NotificationsAnnouncementsTab })));

const TABS = [
  { id: 'inbox', label: 'Inbox', icon: Inbox },
  { id: 'archive', label: 'Archive', icon: Archive },
  { id: 'preferences', label: 'Preferences', icon: Settings },
  { id: 'templates', label: 'Templates', icon: FileText },
  { id: 'announcements', label: 'Announcements', icon: Megaphone },
];

function TabFallback() {
  return (
    <div className="flex justify-center py-16">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

export default function NotificationsPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('inbox');

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

      <Suspense fallback={<TabFallback />}>
        {tab === 'inbox' && <NotificationsInboxTab orgId={orgId} />}
        {tab === 'archive' && <NotificationsArchivedTab orgId={orgId} />}
        {tab === 'preferences' && <NotificationsPreferencesTab />}
        {tab === 'templates' && <NotificationsTemplatesTab orgId={orgId} />}
        {tab === 'announcements' && <NotificationsAnnouncementsTab orgId={orgId} />}
      </Suspense>
    </div>
    </ErrorBoundary>
  );
}
