'use client';

import { Suspense, lazy, useState } from 'react';
import { Loader2, Plus, Zap, Target, Users, Lightbulb, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useOrg } from '@/lib/org';
import {
  useGenerateRecommendations, useEvaluateRules,
} from '@/features/campaigns/api/useAutomation';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const AutomationRulesTab = lazy(() => import('./AutomationRulesTab').then(m => ({ default: m.AutomationRulesTab })));
const AutomationBudgetTab = lazy(() => import('./AutomationBudgetTab').then(m => ({ default: m.AutomationBudgetTab })));
const AutomationBiddingTab = lazy(() => import('./AutomationBiddingTab').then(m => ({ default: m.AutomationBiddingTab })));
const AutomationAudienceTab = lazy(() => import('./AutomationAudienceTab').then(m => ({ default: m.AutomationAudienceTab })));
const AutomationRecommendationsTab = lazy(() => import('./AutomationRecommendationsTab').then(m => ({ default: m.AutomationRecommendationsTab })));

const TABS = [
  { id: 'rules', label: 'Automation Rules', icon: Brain },
  { id: 'budget', label: 'Budget Allocation', icon: Zap },
  { id: 'bids', label: 'Bid Optimization', icon: Target },
  { id: 'audience', label: 'Audience Segments', icon: Users },
  { id: 'recommendations', label: 'Recommendations', icon: Lightbulb },
];

function TabFallback() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

export default function AutomationPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('rules');
  const [showNewRule, setShowNewRule] = useState(false);

  const genRecs = useGenerateRecommendations(orgId);
  const evalRules = useEvaluateRules(orgId);

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Campaign Automation</h1>
          <p className="text-sm text-muted-foreground">
            AI-powered rules, budget allocation, and recommendations
          </p>
        </div>
        <div className="flex items-center gap-3">
          {tab === 'rules' && (
            <>
              <Button variant="outline" size="sm" onClick={() => evalRules.mutate()} disabled={evalRules.isPending}>
                {evalRules.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                Evaluate Rules
              </Button>
              <Button size="sm" onClick={() => setShowNewRule(!showNewRule)}>
                <Plus className="mr-1 h-3 w-3" />
                New Rule
              </Button>
            </>
          )}
          {tab === 'recommendations' && (
            <Button size="sm" onClick={() => genRecs.mutate(undefined)} disabled={genRecs.isPending}>
              {genRecs.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              Generate Recommendations
            </Button>
          )}
        </div>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === t.id
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      <Suspense fallback={<TabFallback />}>
        {tab === 'rules' && (
          <AutomationRulesTab orgId={orgId} showNewRule={showNewRule} setShowNewRule={setShowNewRule} />
        )}
        {tab === 'budget' && (
          <AutomationBudgetTab orgId={orgId} />
        )}
        {tab === 'bids' && (
          <AutomationBiddingTab orgId={orgId} />
        )}
        {tab === 'audience' && (
          <AutomationAudienceTab orgId={orgId} />
        )}
        {tab === 'recommendations' && (
          <AutomationRecommendationsTab orgId={orgId} />
        )}
      </Suspense>
    </div>
    </ErrorBoundary>
  );
}
