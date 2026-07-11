'use client';

import { Users } from 'lucide-react';
import { useAudienceSegments } from '@/features/campaigns/api/useAutomation';

export function AutomationAudienceTab({ orgId }: { orgId: string }) {
  const { data: segments } = useAudienceSegments(orgId);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Manage audience segments with AI-predicted sizing
      </p>
      {segments && segments.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {segments.map((s) => (
            <div key={s.id} className="rounded-lg border bg-card p-4 space-y-3">
              <div>
                <p className="font-medium text-sm">{s.name}</p>
                <p className="text-xs text-muted-foreground">Source: {s.source}</p>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Predicted Size</span>
                <span className="font-medium">{s.predicted_size.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-medium">{(s.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-secondary">
                <div className="h-full rounded-full bg-primary" style={{ width: `${s.confidence_score * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Users className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No segments yet</p>
        </div>
      )}
    </div>
  );
}
