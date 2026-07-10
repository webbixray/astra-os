'use client';

import { useState } from 'react';
import { Loader2, Plus, Zap, Target, Users, Lightbulb, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useOrg } from '@/lib/org';
import {
  useBudgetRules, useCalculateAllocation,
  useBidRules,
  useAudienceSegments,
  useRecommendations, useGenerateRecommendations, useApplyRecommendation,
  useAutomationRules, useCreateAutomationRule, useToggleAutomationRule,
  useEvaluateRules, useDeleteAutomationRule,
} from '@/features/campaigns/api/useAutomation';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const TABS = [
  { id: 'rules', label: 'Automation Rules', icon: Brain },
  { id: 'budget', label: 'Budget Allocation', icon: Zap },
  { id: 'bids', label: 'Bid Optimization', icon: Target },
  { id: 'audience', label: 'Audience Segments', icon: Users },
  { id: 'recommendations', label: 'Recommendations', icon: Lightbulb },
];

const TRIGGER_TYPES = [
  'schedule', 'metric_threshold', 'budget_exhausted',
  'performance_drop', 'anomaly_detected', 'campaign_status_change',
];
const ACTION_TYPES = [
  'adjust_budget', 'adjust_bid', 'pause_campaign', 'activate_campaign',
  'change_channel_allocation', 'send_notification', 'create_content',
];

export default function AutomationPage() {
  const { orgId } = useOrg();
  const [tab, setTab] = useState('rules');

  const { data: budgetRules } = useBudgetRules(orgId);
  const calcAllocation = useCalculateAllocation();

  const { data: bidRules } = useBidRules(orgId);

  const { data: segments } = useAudienceSegments(orgId);

  const { data: recommendations } = useRecommendations(orgId);
  const genRecs = useGenerateRecommendations(orgId);
  const applyRec = useApplyRecommendation();

  const { data: rules } = useAutomationRules(orgId);
  const createRule = useCreateAutomationRule(orgId);
  const toggleRule = useToggleAutomationRule();
  const evalRules = useEvaluateRules(orgId);
  const deleteRule = useDeleteAutomationRule();

  const [showNewRule, setShowNewRule] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', trigger_type: 'schedule', action_type: 'adjust_budget', description: '' });

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

      {/* Automation Rules */}
      {tab === 'rules' && (
        <div className="space-y-4">
          {showNewRule && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium">New Automation Rule</h3>
              <label htmlFor="rule-name" className="text-xs font-medium text-muted-foreground">Rule name</label>
              <Input id="rule-name" placeholder="Rule name" value={newRule.name}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })} />
              <label htmlFor="rule-desc" className="text-xs font-medium text-muted-foreground">Description</label>
              <Textarea id="rule-desc" placeholder="Description" value={newRule.description}
                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })} rows={2} />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-muted-foreground">Trigger Type</label>
                  <Select value={newRule.trigger_type}
                    onChange={(e) => setNewRule({ ...newRule, trigger_type: e.target.value })}
                    options={TRIGGER_TYPES.map((t) => ({ value: t, label: t.replace(/_/g, ' ') }))} />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Action Type</label>
                  <Select value={newRule.action_type}
                    onChange={(e) => setNewRule({ ...newRule, action_type: e.target.value })}
                    options={ACTION_TYPES.map((a) => ({ value: a, label: a.replace(/_/g, ' ') }))} />
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" disabled={createRule.isPending || !newRule.name}
                  onClick={async () => {
                    await createRule.mutateAsync(newRule);
                    setShowNewRule(false);
                    setNewRule({ name: '', trigger_type: 'schedule', action_type: 'adjust_budget', description: '' });
                  }}>
                  {createRule.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                  Save Rule
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowNewRule(false)}>Cancel</Button>
              </div>
            </div>
          )}

          {rules && rules.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground min-w-[700px]">
                <span className="col-span-2">Name</span>
                <span>Trigger</span>
                <span>Action</span>
                <span>Status</span>
                <span>Executions</span>
                <span></span>
              </div>
              {rules.map((r) => (
                <div key={r.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-2 border-b px-4 py-3 text-sm items-center last:border-0 min-w-[700px]">
                  <span className="col-span-2 font-medium">{r.name}</span>
                  <span className="text-muted-foreground">{r.trigger_type.replace(/_/g, ' ')}</span>
                  <span className="text-muted-foreground">{r.action_type.replace(/_/g, ' ')}</span>
                  <span>
                    <button
                      onClick={() => toggleRule.mutate({ ruleId: r.id, enabled: !r.enabled })}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        r.enabled ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {r.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </span>
                  <span className="text-muted-foreground">{r.execution_count}</span>
                  <div className="flex justify-end gap-1">
                    <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500" aria-label="Delete"
                      onClick={() => deleteRule.mutate(r.id)}>×</Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <Brain className="h-10 w-10 text-muted-foreground/40" />
              <p className="text-lg text-muted-foreground">No automation rules yet</p>
              <p className="text-sm text-muted-foreground">Create rules to automatically manage campaigns</p>
              <Button variant="outline" onClick={() => setShowNewRule(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Rule
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Budget Allocation */}
      {tab === 'budget' && (
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
      )}

      {/* Bid Optimization */}
      {tab === 'bids' && (
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
      )}

      {/* Audience Segments */}
      {tab === 'audience' && (
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
      )}

      {/* Recommendations */}
      {tab === 'recommendations' && (
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
      )}
    </div>
    </ErrorBoundary>
  );
}
