'use client';

import { cn } from '@/lib/utils';
import { useChangeBillingPlan } from '@/features/organizations/api/useOrganizations';

const PLAN_OPTIONS = [
  { value: 'free', label: 'Free' },
  { value: 'starter', label: 'Starter' },
  { value: 'professional', label: 'Professional' },
  { value: 'business', label: 'Business' },
  { value: 'enterprise', label: 'Enterprise' },
];

interface SettingsBillingTabProps {
  orgId: string;
  billing: any;
}

export function SettingsBillingTab({ orgId, billing }: SettingsBillingTabProps) {
  const changePlan = useChangeBillingPlan();

  if (!billing) return null;

  return (
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
  );
}
