'use client';

import { Target } from 'lucide-react';
import { useBidRules } from '@/features/campaigns/api/useAutomation';

export function AutomationBiddingTab({ orgId }: { orgId: string }) {
  const { data: bidRules } = useBidRules(orgId);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Configure bid strategies for automated ad pricing
      </p>
      {bidRules && bidRules.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground min-w-[600px]">
            <span className="col-span-2">Name</span>
            <span>Strategy</span>
            <span>Target</span>
            <span>Range</span>
            <span>Status</span>
          </div>
          {bidRules.map((r) => (
            <div key={r.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 border-b px-4 py-3 text-sm items-center last:border-0 min-w-[600px]">
              <span className="col-span-2 font-medium">{r.name}</span>
              <span className="text-muted-foreground">{r.strategy.replace(/_/g, ' ')}</span>
              <span>{r.target_value}</span>
              <span className="text-xs text-muted-foreground">{r.min_bid} – {r.max_bid}</span>
              <span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  r.enabled ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'
                }`}>{r.enabled ? 'Active' : 'Disabled'}</span>
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Target className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No bid rules yet</p>
        </div>
      )}
    </div>
  );
}
