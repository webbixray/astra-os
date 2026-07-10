'use client';

import { useState } from 'react';
import { z } from 'zod';
import {
  Settings,
  Building2,
  CreditCard,
  Flag,
  BarChart3,
  Plus,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import {
  useOrgTree,
  useCreateSubOrg,
  useFeatureFlags,
  useSetFeatureFlag,
  useUsageSummary,
  useBillingPlan,
  useChangeBillingPlan,
} from '@/features/organizations/api/useOrganizations';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const subOrgSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
  slug: z.string().min(1, 'Slug is required').regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Slug must be lowercase alphanumeric with hyphens'),
});

const PLAN_OPTIONS = [
  { value: 'free', label: 'Free' },
  { value: 'starter', label: 'Starter' },
  { value: 'professional', label: 'Professional' },
  { value: 'business', label: 'Business' },
  { value: 'enterprise', label: 'Enterprise' },
];

const FEATURE_PRESETS = [
  { key: 'advanced_analytics', label: 'Advanced Analytics' },
  { key: 'custom_reports', label: 'Custom Reports' },
  { key: 'abi_testing', label: 'A/B Testing' },
  { key: 'multi_channel_publishing', label: 'Multi-Channel Publishing' },
  { key: 'email_marketing', label: 'Email Marketing' },
  { key: 'workflow_automation', label: 'Workflow Automation' },
  { key: 'api_access', label: 'API Access' },
  { key: 'white_label', label: 'White Label' },
];

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const { orgId } = useOrg();

  const [tab, setTab] = useState('org');
  const [showCreateSub, setShowCreateSub] = useState(false);
  const [subName, setSubName] = useState('');
  const [subSlug, setSubSlug] = useState('');
  const [subErrors, setSubErrors] = useState<{ name?: string; slug?: string }>({});
  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());

  const { data: orgTree } = useOrgTree(orgId);
  const { data: features } = useFeatureFlags(orgId);
  const { data: usage } = useUsageSummary(orgId);
  const { data: billing } = useBillingPlan(orgId);

  const createSubOrg = useCreateSubOrg();
  const setFeatureFlag = useSetFeatureFlag();
  const changePlan = useChangeBillingPlan();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleCreateSub = () => {
    const result = subOrgSchema.safeParse({ name: subName.trim(), slug: subSlug.trim() });
    if (!result.success) {
      const fieldErrors = result.error.flatten().fieldErrors;
      setSubErrors({
        name: fieldErrors.name?.[0],
        slug: fieldErrors.slug?.[0],
      });
      return;
    }
    setSubErrors({});
    createSubOrg.mutate(
      { orgId, name: result.data.name, slug: result.data.slug },
      { onSuccess: () => { setShowCreateSub(false); setSubName(''); setSubSlug(''); setSubErrors({}); } },
    );
  };

  const toggleOrg = (id: string) => {
    setExpandedOrgs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
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
          {tab === 'org' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-lg font-semibold">Organization Hierarchy</h2>
                <p className="text-sm text-muted-foreground">Manage parent/child orgs</p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                {orgTree && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <button onClick={() => toggleOrg(orgTree.id)} className="cursor-pointer" aria-label="Toggle">
                        {expandedOrgs.has(orgTree.id)
                          ? <ChevronDown className="h-4 w-4" />
                          : <ChevronRight className="h-4 w-4" />}
                      </button>
                      <Building2 className="h-4 w-4" />
                      <span className="font-medium">{orgTree.name}</span>
                      <span className="text-xs text-muted-foreground">({orgTree.plan_tier})</span>
                    </div>
                    {expandedOrgs.has(orgTree.id) && orgTree.children.length > 0 && (
                      <div className="ml-6 space-y-1 border-l pl-4">
                        {orgTree.children.map((child) => (
                          <div key={child.id} className="flex items-center gap-2 py-1 text-sm">
                            <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                            <span>{child.name}</span>
                            <span className="text-xs text-muted-foreground">({child.plan_tier})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {showCreateSub ? (
                  <div className="mt-4 space-y-3 rounded-md border p-3">
                    <div className="space-y-1">
                      <Input
                        placeholder="Organization name"
                        aria-label="Organization name"
                        value={subName}
                        onChange={(e) => { setSubName(e.target.value); setSubErrors((prev) => ({ ...prev, name: undefined })); }}
                        error={subErrors.name}
                      />
                      {subErrors.name && <p className="text-xs text-destructive">{subErrors.name}</p>}
                    </div>
                    <div className="space-y-1">
                      <Input
                        placeholder="slug (e.g., my-org)"
                        aria-label="Organization slug"
                        value={subSlug}
                        onChange={(e) => { setSubSlug(e.target.value); setSubErrors((prev) => ({ ...prev, slug: undefined })); }}
                        error={subErrors.slug}
                      />
                      {subErrors.slug && <p className="text-xs text-destructive">{subErrors.slug}</p>}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={handleCreateSub} disabled={createSubOrg.isPending}>
                        Create Sub-Org
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setShowCreateSub(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button size="sm" variant="outline" className="mt-4" onClick={() => setShowCreateSub(true)}>
                    <Plus className="mr-1 h-3.5 w-3.5" />
                    Create Sub-Organization
                  </Button>
                )}
              </div>

              <div className="rounded-lg border bg-card p-4">
                <h3 className="text-sm font-medium mb-2">Current Organization</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span>{orgTree?.name ?? '—'}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Slug</span><span>{orgTree?.slug ?? '—'}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Plan</span><span className="capitalize">{orgTree?.plan_tier ?? '—'}</span></div>
                </div>
              </div>
            </div>
          )}

          {tab === 'billing' && billing && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-lg font-semibold">Billing & Plan</h2>
                <p className="text-sm text-muted-foreground">Manage your subscription and plan limits</p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm font-medium">Current Plan</p>
                    <p className="text-2xl font-bold capitalize">{billing.plan_tier}</p>
                  </div>
                  <span className={cn(
                    'rounded-full px-3 py-1 text-xs font-medium',
                    billing.subscription_status === 'active' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500',
                  )}>
                    {billing.subscription_status}
                  </span>
                </div>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Billing cycle</span>
                    <span className="capitalize">{billing.billing_cycle}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Period start</span>
                    <span>{new Date(billing.current_period_start).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Period end</span>
                    <span>{new Date(billing.current_period_end).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <h3 className="text-sm font-medium mb-3">Change Plan</h3>
                <div className="grid grid-cols-5 gap-2">
                  {PLAN_OPTIONS.map((p) => (
                    <button
                      key={p.value}
                      onClick={() => changePlan.mutate({ orgId, plan_tier: p.value })}
                      className={cn(
                        'rounded-md border px-3 py-2 text-sm transition-colors',
                        billing.plan_tier === p.value
                          ? 'border-primary bg-primary/10 font-medium'
                          : 'hover:bg-accent',
                      )}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <h3 className="text-sm font-medium mb-3">Plan Limits</h3>
                <div className="space-y-2 text-sm">
                  {Object.entries(billing.limits).map(([key, val]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground">{key.replace(/_/g, ' ')}</span>
                      <span>{val === -1 ? 'Unlimited' : String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === 'features' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-lg font-semibold">Feature Flags</h2>
                <p className="text-sm text-muted-foreground">Enable or disable features for this organization</p>
              </div>

              <div className="rounded-lg border bg-card">
                {FEATURE_PRESETS.map((preset) => {
                  const flag = features?.find((f) => f.feature_key === preset.key);
                  const enabled = flag?.enabled ?? false;
                  return (
                    <div key={preset.key} className="flex items-center justify-between border-b px-4 py-3 last:border-0">
                      <span className="text-sm">{preset.label}</span>
                      <button
                        onClick={() => setFeatureFlag.mutate({
                          orgId,
                          feature_key: preset.key,
                          enabled: !enabled,
                        })}
                        className={cn(
                          'relative h-6 w-11 rounded-full transition-colors',
                          enabled ? 'bg-primary' : 'bg-muted',
                        )}
                      >
                        <span className={cn(
                          'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-card transition-transform shadow-sm',
                          enabled && 'translate-x-5',
                        )} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {tab === 'usage' && usage && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-lg font-semibold">Usage & Limits</h2>
                <p className="text-sm text-muted-foreground">
                  Current billing period usage for {usage.plan_tier} plan
                </p>
              </div>

              <div className="space-y-3">
                {Object.entries(usage.usage).map(([metric, value]) => {
                  const limit = usage.limits[metric];
                  const isUnlimited = limit === -1;
                  const pct = isUnlimited ? 0 : limit ? (value as number) / (limit as number) * 100 : 0;
                  return (
                    <div key={metric} className="rounded-lg border bg-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium capitalize">
                          {metric.replace(/_/g, ' ')}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {typeof value === 'number' ? value.toLocaleString() : value}
                          {!isUnlimited && ` / ${(limit as number).toLocaleString()}`}
                        </span>
                      </div>
                      {!isUnlimited && (
                        <div className="h-2 rounded-full bg-muted">
                          <div
                            className={cn(
                              'h-full rounded-full transition-all',
                              pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-yellow-500' : 'bg-primary',
                            )}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {tab === 'profile' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-lg font-semibold">Profile</h2>
                <p className="text-sm text-muted-foreground">Your account details</p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <div className="space-y-3 text-sm">
                  <div><span className="text-muted-foreground">Name</span><p className="font-medium">{user?.name ?? 'Not set'}</p></div>
                  <div><span className="text-muted-foreground">Email</span><p className="font-medium">{user?.email ?? 'Not set'}</p></div>
                </div>
              </div>

              <div className="rounded-lg border border-destructive/20 bg-card p-4">
                <h3 className="mb-2 text-sm font-medium text-destructive">Danger Zone</h3>
                <p className="mb-3 text-sm text-muted-foreground">Sign out of your account</p>
                <Button variant="destructive" size="sm" onClick={handleLogout}>Sign Out</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );

}
