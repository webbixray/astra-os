'use client';

import { useState } from 'react';
import { Loader2, Plus, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  useAutomationRules, useCreateAutomationRule, useToggleAutomationRule,
  useDeleteAutomationRule,
} from '@/features/campaigns/api/useAutomation';

const TRIGGER_TYPES = [
  'schedule', 'metric_threshold', 'budget_exhausted',
  'performance_drop', 'anomaly_detected', 'campaign_status_change',
];
const ACTION_TYPES = [
  'adjust_budget', 'adjust_bid', 'pause_campaign', 'activate_campaign',
  'change_channel_allocation', 'send_notification', 'create_content',
];

export function AutomationRulesTab({ orgId, showNewRule, setShowNewRule }: {
  orgId: string;
  showNewRule: boolean;
  setShowNewRule: (v: boolean) => void;
}) {
  const { data: rules } = useAutomationRules(orgId);
  const createRule = useCreateAutomationRule(orgId);
  const toggleRule = useToggleAutomationRule();
  const deleteRule = useDeleteAutomationRule();

  const [newRule, setNewRule] = useState({ name: '', trigger_type: 'schedule', action_type: 'adjust_budget', description: '' });

  return (
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
  );
}
