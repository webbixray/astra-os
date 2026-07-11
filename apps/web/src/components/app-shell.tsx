'use client';

import { memo, useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Target,
  FileText,
  TrendingUp,
  Workflow,
  Settings,
  Command,
  Globe,
  CalendarDays,
  Users,
  Sparkles,
  Bell,
  Inbox,
  Send,
  Mail,
  Zap,
  Activity,
  CheckCheck,
  Moon,
  Sun,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  useNotifications,
  useUnreadCount,
  useMarkRead,
  useMarkAllRead,
} from '@/features/notifications/api/useNotifications';
import { useNotificationStream } from '@/hooks/useNotificationStream';
import { useAuth } from '@/lib/auth';
import { useOrg } from '@/lib/org';
import { useTheme } from '@/lib/theme';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Campaigns', href: '/campaigns', icon: Target },
  { name: 'Content', href: '/content', icon: FileText },
  { name: 'AI Content', href: '/ai-content', icon: Sparkles },
  { name: 'Calendar', href: '/calendar', icon: CalendarDays },
  { name: 'Notifications', href: '/notifications', icon: Inbox },
  { name: 'Analytics', href: '/analytics', icon: TrendingUp },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'Ad Accounts', href: '/advertising', icon: Globe },
  { name: 'Publishing', href: '/content/queue', icon: Send },
  { name: 'Email', href: '/email/campaigns', icon: Mail },
  { name: 'Automation', href: '/automation', icon: Zap },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Reports', href: '/reports', icon: TrendingUp },
  { name: 'Team', href: '/team', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const TYPE_ICONS: Record<string, string> = {
  approval_request: '🔔',
  workflow_completed: '✅',
  workflow_failed: '❌',
  campaign_milestone: '🎯',
  ad_sync_completed: '🔄',
  content_published: '📝',
  member_joined: '👋',
  report_ready: '📊',
};

const SidebarNav = memo(function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
      {navigation.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link key={item.name} href={item.href} aria-current={isActive ? 'page' : undefined}>
            <span
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </span>
          </Link>
        );
      })}
    </nav>
  );
});

const UserMenu = memo(function UserMenu() {
  const { user, logout } = useAuth();
  const { currentOrg } = useOrg();
  return (
    <div className="border-t border-border p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-sm font-medium" aria-hidden="true">
          {user?.name?.charAt(0)?.toUpperCase() || 'U'}
        </div>
        <div className="flex-1 truncate text-sm">
          <p className="font-medium">{user?.name || 'User'}</p>
          <p className="text-xs text-muted-foreground">
            {currentOrg?.plan_tier || 'Free'} Plan
          </p>
        </div>
        <button
          onClick={logout}
          className="text-xs text-muted-foreground hover:text-foreground"
          aria-label="Sign out"
        >
          Sign out
        </button>
      </div>
    </div>
  );
});

const NotificationBell = memo(function NotificationBell() {
  const { orgId } = useOrg();
  const { data: unreadData } = useUnreadCount(orgId);
  const { data: recentNotifications } = useNotifications(orgId, true, 5);
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useNotificationStream(orgId);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Notifications"
        aria-haspopup="true"
        aria-expanded={showDropdown}
        onClick={() => setShowDropdown(!showDropdown)}
      >
        <Bell className="h-5 w-5" />
        {(unreadData?.unread_count || 0) > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-primary-foreground">
            {Math.min(unreadData?.unread_count || 0, 99)}
          </span>
        )}
      </Button>

      {showDropdown && (
        <div className="absolute right-0 top-10 z-50 w-80 rounded-lg border bg-card shadow-lg" role="menu" aria-label="Notifications">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <span className="text-sm font-medium">Notifications</span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => { markAllRead.mutate(orgId); }}
            >
              <CheckCheck className="mr-1 h-3 w-3" />
              Mark all read
            </Button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {recentNotifications && recentNotifications.length > 0 ? (
              recentNotifications.map((n) => (
                <div
                  key={n.id}
                  role="menuitem"
                  tabIndex={0}
                  className="flex items-start gap-3 border-b px-4 py-3 text-sm hover:bg-accent/50 cursor-pointer transition-colors"
                  onClick={() => {
                    if (!n.is_read) markRead.mutate(n.id);
                    setShowDropdown(false);
                  }}
                >
                  <span className="mt-0.5 text-base">
                    {TYPE_ICONS[n.type] || '📬'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{n.title}</p>
                    {n.body && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {n.body}
                      </p>
                    )}
                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      {new Date(n.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-8 text-center text-sm text-muted-foreground">
                <Bell className="mb-2 h-6 w-6" />
                No notifications
              </div>
            )}
          </div>
          <Link
            href="/notifications"
            className="block border-t px-4 py-2 text-center text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setShowDropdown(false)}
          >
            View all notifications
          </Link>
        </div>
      )}
    </div>
  );
});

export function AppShell({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();
  const { orgId } = useOrg();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-primary focus:text-primary-foreground focus:px-4 focus:py-2 focus:m-2 focus:rounded-md"
      >
        Skip to content
      </a>
      <aside className="flex w-64 flex-col border-r border-border" aria-label="Sidebar">
        <div className="flex h-14 items-center gap-2 border-b border-border px-6">
          <Command className="h-5 w-5" />
          <span className="font-semibold">ASTRA OS</span>
        </div>
        <SidebarNav />
        <UserMenu />
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center gap-4 border-b border-border px-6" aria-label="Top bar">
          <div className="relative flex-1">
            <Command className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Ask AI anything... (Cmd+K)"
              aria-label="Ask AI anything"
              className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-4 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            onClick={toggleTheme}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
          {orgId && <NotificationBell />}
        </header>
        <main id="main-content" className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
