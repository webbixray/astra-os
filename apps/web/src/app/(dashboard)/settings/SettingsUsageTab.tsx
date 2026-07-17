'use client';

import { cn } from '@/lib/utils';

interface SettingsUsageTabProps {
  usage: any;
}

export function SettingsUsageTab({ usage }: SettingsUsageTabProps) {
  if (!usage) return null;

  return (
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
                  {typeof value === 'number' ? value.toLocaleString() : String(value ?? '')}
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
  );
}
