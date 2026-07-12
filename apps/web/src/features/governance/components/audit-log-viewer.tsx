'use client';

import { useState } from 'react';
import {
  useAgentActions,
  useActionExplanation,
  useAuditSummary,
} from '../api/useAutonomy';
import {
  AUTONOMY_LEVEL_LABELS,
  AUTONOMY_LEVEL_COLORS,
  STATUS_COLORS,
  type AgentAction,
  type ActionExplanation,
} from '../types';

interface AuditLogViewerProps {
  organizationId: string;
}

export function AuditLogViewer({ organizationId }: AuditLogViewerProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [filterAgentType, setFilterAgentType] = useState<string>('');
  const [filterAction, setFilterAction] = useState<string>('');

  const { data: actionsData, isLoading } = useAgentActions(
    organizationId,
    {
      agentType: filterAgentType || undefined,
      actionName: filterAction || undefined,
      limit: 50,
    },
  );

  const { data: summary } = useAuditSummary(organizationId);

  const actions = actionsData?.items || [];

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Audit Log & Explainability
      </h2>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Total Actions"
            value={summary.total_actions.toString()}
          />
          <SummaryCard
            label="Successful"
            value={summary.successful.toString()}
            color="text-green-600"
          />
          <SummaryCard
            label="Failed"
            value={summary.failed.toString()}
            color="text-red-600"
          />
          <SummaryCard
            label="Auto-Executed"
            value={summary.auto_executed.toString()}
            color="text-blue-600"
          />
          <SummaryCard
            label="Human Approved"
            value={summary.human_approved.toString()}
            color="text-purple-600"
          />
          <SummaryCard
            label="Total Cost"
            value={`$${summary.total_cost_usd.toFixed(4)}`}
          />
          <SummaryCard
            label="Total Tokens"
            value={summary.total_tokens.toLocaleString()}
          />
          <SummaryCard
            label="Autonomy Levels"
            value={Object.entries(summary.by_autonomy_level)
              .map(([k, v]) => `${k}: ${v}`)
              .join(', ')}
            small
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filterAgentType}
          onChange={(e) => setFilterAgentType(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Agent Types</option>
          <option value="ContentSpecialist">Content Specialist</option>
          <option value="AdvertisingDirector">Advertising Director</option>
          <option value="CreativeDirector">Creative Director</option>
          <option value="AnalyticsDirector">Analytics Director</option>
          <option value="ResearchDirector">Research Director</option>
        </select>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Actions</option>
          <option value="content.generate">Content Generate</option>
          <option value="campaign.launch">Campaign Launch</option>
          <option value="campaign.pause">Campaign Pause</option>
          <option value="analytics.report">Analytics Report</option>
        </select>
      </div>

      {/* Action List */}
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Agent
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Action
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Autonomy
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Cost
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Time
              </th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            ) : actions.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No actions recorded yet.
                </td>
              </tr>
            ) : (
              actions.map((action) => (
                <tr
                  key={action.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => setSelectedAction(action.id)}
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900">
                      {action.agent_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600">{action.action}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        action.success
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {action.success ? 'Success' : 'Failed'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        AUTONOMY_LEVEL_COLORS[action.autonomy_level] || ''
                      }`}
                    >
                      {AUTONOMY_LEVEL_LABELS[action.autonomy_level] ||
                        `Level ${action.autonomy_level}`}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    ${action.cost_usd.toFixed(4)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(action.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-blue-600">Explain →</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Explanation Panel */}
      {selectedAction && (
        <ExplanationPanel actionId={selectedAction} />
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
  small,
}: {
  label: string;
  value: string;
  color?: string;
  small?: boolean;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p
        className={`mt-1 font-semibold ${color || 'text-gray-900'} ${small ? 'text-xs' : 'text-lg'}`}
      >
        {value}
      </p>
    </div>
  );
}

function ExplanationPanel({ actionId }: { actionId: string }) {
  const { data: explanation, isLoading } = useActionExplanation(actionId);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <p className="text-sm text-blue-600">Loading explanation…</p>
      </div>
    );
  }

  if (!explanation) return null;

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Decision Explanation</h3>
        <button
          onClick={() => {}}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          Close
        </button>
      </div>

      {/* One-liner */}
      <div className="mb-4 rounded-md bg-white p-3">
        <p className="text-sm font-medium text-gray-900">{explanation.one_line}</p>
      </div>

      {/* Paragraph */}
      <div className="mb-4">
        <h4 className="mb-1 text-xs font-medium uppercase text-gray-500">
          Summary
        </h4>
        <p className="text-sm text-gray-700">{explanation.paragraph}</p>
      </div>

      {/* Reasoning Steps */}
      {explanation.reasoning_steps.length > 0 && (
        <div className="mb-4">
          <h4 className="mb-2 text-xs font-medium uppercase text-gray-500">
            Reasoning Steps
          </h4>
          <div className="space-y-2">
            {explanation.reasoning_steps.map((step, i) => (
              <div
                key={i}
                className="flex gap-3 rounded-md bg-white p-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-700">
                  {step.step}
                </span>
                <div className="text-sm">
                  <p className="text-gray-700">{step.thought}</p>
                  {step.action && (
                    <p className="mt-1 text-xs text-gray-500">
                      Action: {step.action}
                    </p>
                  )}
                  {step.result && (
                    <p className="mt-1 text-xs text-gray-500">
                      Result: {step.result}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Autonomy Context */}
      <div className="flex gap-4 text-xs text-gray-500">
        <span>
          Level:{' '}
          {AUTONOMY_LEVEL_LABELS[explanation.autonomy_context.level] ||
            `Level ${explanation.autonomy_context.level}`}
        </span>
        <span>
          Auto-executed: {explanation.autonomy_context.was_auto_executed ? 'Yes' : 'No'}
        </span>
        <span>
          Required approval: {explanation.autonomy_context.had_approval_request ? 'Yes' : 'No'}
        </span>
      </div>
    </div>
  );
}
