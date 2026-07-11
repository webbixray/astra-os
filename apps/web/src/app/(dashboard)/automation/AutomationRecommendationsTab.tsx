'use client';

import { Loader2, Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useRecommendations, useGenerateRecommendations, useApplyRecommendation,
} from '@/features/campaigns/api/useAutomation';

export function AutomationRecommendationsTab({ orgId }: { orgId: string }) {
  const { data: recommendations } = useRecommendations(orgId);
  const genRecs = useGenerateRecommendations(orgId);
  const applyRec = useApplyRecommendation();

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        AI-generated content and strategy recommendations
      </p>
      {recommendations && recommendations.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {recommendations.map((r) => (
            <div key={r.id} className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium">
                    {r.type.replace(/_/g, ' ')}
                  </span>
                  <p className="mt-2 font-medium text-sm">{r.title}</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-medium">{(r.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-secondary">
                <div className="h-full rounded-full bg-primary" style={{ width: `${r.confidence_score * 100}%` }} />
              </div>
              <div className="flex gap-2">
                <Button size="sm" className="flex-1 text-xs"
                  onClick={() => applyRec.mutate(r.id)}
                  disabled={r.applied || applyRec.isPending}>
                  {r.applied ? 'Applied' : 'Apply'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Lightbulb className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No recommendations yet</p>
          <p className="text-sm text-muted-foreground">Generate AI recommendations for your campaigns</p>
          <Button variant="outline" onClick={() => genRecs.mutate(undefined)} disabled={genRecs.isPending}>
            {genRecs.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
            Generate Now
          </Button>
        </div>
      )}
    </div>
  );
}
