'use client';

import { Suspense, lazy, useState } from 'react';
import {
  Settings,
  Building2,
  CreditCard,
  Flag,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import {
  useOrgTree,
  useFeatureFlags,
  useUsageSummary,
  useBillingPlan,
} from '@/features/organizations/api/useOrganizations';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const SettingsOrgTab = lazy(() => import('./SettingsOrgTab').then(m => ({ default: m.SettingsOrgTab })));
const SettingsBillingTab = lazy(() => import('./SettingsBillingTab').then(m => ({ default: m.SettingsBillingTab })));
const SettingsFeaturesTab = lazy(() => import('./SettingsFeaturesTab').then(m => ({ default: m.SettingsFeaturesTab })));
const SettingsUsageTab = lazy(() => import('./SettingsUsageTab').then(m => ({ default: m.SettingsUsageTab })));
const SettingsProfileTab = lazy(() => import('./SettingsProfileTab').then(m => ({ default: m.SettingsProfileTab })));

function TabSkeleton() {
  return (
    <div className="max-w-2xl space-y-6 animate-pulse">
      <div className="space-y-2">
        <div className="h-6 w-48 rounded bg-muted" />
        <div className="h-4 w-64 rounded bg-muted" />
      </div>
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="h-4 w-full rounded bg-muted" />
        <div className="h-4 w-3/4 rounded bg-muted" />
        <div className="h-4 w-1/2 rounded bg-muted" />
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const { orgId } = useOrg();

  const [tab, setTab] = useState('org');

  const { data: orgTree } = useOrgTree(orgId);
  const { data: features } = useFeatureFlags(orgId);
  const { data: usage } = useUsageSummary(orgId);
  const { data: billing } = useBillingPlan(orgId);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const tabs = [
    { key: 'org', label: 'Organization', icon: Building2 },
    { key: 'billing', label: 'Billing', icon: CreditCard },
    { key: 'features', label: 'Features', icon: Flag },
    { key: 'usage', label: 'Usage', icon: BarChart3 },
    { key: 'profile', label: 'Profile', icon: Settings },
  ];

  return (
    <ErrorBoundary>
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Settings className="h-5 w-5" />
          <h1 className="text-lg font-semibold">Settings</h1>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Tabs sidebar */}
        <div className="w-48 shrink-0 border-r p-3 space-y-1">
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
          <Suspense fallback={<TabSkeleton />}>
            {tab === 'org' && <SettingsOrgTab orgId={orgId} orgTree={orgTree} />}
            {tab === 'billing' && <SettingsBillingTab orgId={orgId} billing={billing} />}
            {tab === 'features' && <SettingsFeaturesTab orgId={orgId} features={features} />}
            {tab === 'usage' && <SettingsUsageTab usage={usage} />}
            {tab === 'profile' && <SettingsProfileTab user={user} onLogout={handleLogout} />}
          </Suspense>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
