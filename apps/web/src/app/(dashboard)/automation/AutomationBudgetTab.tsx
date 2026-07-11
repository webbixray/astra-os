'use client';

import { Loader2, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useBudgetRules, useCalculateAllocation } from '@/features/campaigns/api/useAutomation';

export function AutomationBudgetTab({ orgId }: { orgId: string }) {
  const { data: budgetRules } = useBudgetRules(orgId);
  const calcAllocation = useCalculateAllocation();

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Define budget allocation rules to distribute spend across campaigns
      </p>
      {budgetRules && budgetRules.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {budgetRules.map((r) => (
            <div key={r.id} className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-sm">{r.name}</p>
                  <p className="text-xs text-muted-foreground">{r.strategy.replace(/_/g, ' ')} strategy</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  r.enabled ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'
                }`}>{r.enabled ? 'Active' : 'Disabled'}</span>
              </div>
              <div className="space-y-1">
                {Object.entries(r.allocations || {}).map(([ch, pct]) => (
                  <div key={ch} className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{ch}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 rounded-full bg-secondary">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="font-medium">{pct}%</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button size="sm" variant="outline" className="w-full text-xs"
                onClick={() => calcAllocation.mutate(r.id)}
                disabled={calcAllocation.isPending}>
                {calcAllocation.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                Calculate Allocation
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Zap className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No budget rules yet</p>
        </div>
      )}
    </div>
  );
}
