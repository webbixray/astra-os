'use client';

import { useState } from 'react';
import {
  useAutonomyConfig,
  useUpdateAutonomyConfig,
} from '../api/useAutonomy';
import {
  AUTONOMY_LEVEL_LABELS,
  AUTONOMY_LEVEL_COLORS,
} from '../types';

interface AutonomySettingsProps {
  organizationId: string;
}

const AGENT_TYPES = [
  'ContentSpecialist',
  'SEOSpecialist',
  'SocialSpecialist',
  'Copywriter',
  'Designer',
  'BrandVoice',
  'CampaignOptimizer',
  'BidManager',
  'AudienceResearcher',
  'MarketResearcher',
  'CompetitorAnalyst',
  'TrendAnalyzer',
  'DataAnalyst',
  'AttributionModeler',
  'ReportGenerator',
  'WorkflowBuilder',
  'AutomationScheduler',
  'IntegrationManager',
  'ContentReviewer',
  'PrivacyAuditor',
  'PolicyEnforcer',
];

export function AutonomySettings({ organizationId }: AutonomySettingsProps) {
  const { data: config, isLoading } = useAutonomyConfig(organizationId);
  const updateMutation = useUpdateAutonomyConfig();
  const [localConfig, setLocalConfig] = useState<{
    defaultLevel: number;
    agentLevels: Record<string, number>;
    spendLimit: number;
  } | null>(null);

  const activeConfig = localConfig || (config ? {
    defaultLevel: config.default_level,
    agentLevels: { ...config.agent_levels },
    spendLimit: config.auto_approve_spend_limit,
  } : null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (!activeConfig) return null;

  const handleSave = async () => {
    try {
      await updateMutation.mutateAsync({
        organizationId,
        defaultLevel: activeConfig.defaultLevel,
        agentLevels: activeConfig.agentLevels,
        autoApproveSpendLimit: activeConfig.spendLimit,
      });
      setLocalConfig(null); // Clear local state after save
    } catch (err) {
      console.error('Update failed:', err);
    }
  };

  const setDefaultLevel = (level: number) => {
    setLocalConfig({
      ...activeConfig,
      defaultLevel: level,
    });
  };

  const setAgentLevel = (agentType: string, level: number) => {
    setLocalConfig({
      ...activeConfig,
      agentLevels: {
        ...activeConfig.agentLevels,
        [agentType]: level,
      },
    });
  };

  const hasChanges = localConfig !== null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Autonomy Settings
        </h2>
        {hasChanges && (
          <button
            onClick={handleSave}
            disabled={updateMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
          </button>
        )}
      </div>

      {/* Default Level */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-700">
          Default Autonomy Level
        </h3>
        <p className="mb-3 text-xs text-gray-500">
          Applied to all agents unless overridden below.
        </p>
        <div className="flex gap-2">
          {([0, 1, 2] as const).map((level) => (
            <button
              key={level}
              onClick={() => setDefaultLevel(level)}
              className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                activeConfig.defaultLevel === level
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {AUTONOMY_LEVEL_LABELS[level]}
            </button>
          ))}
        </div>
      </div>

      {/* Spend Limit */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-2 text-sm font-medium text-gray-700">
          Auto-Approve Spend Limit
        </h3>
        <p className="mb-3 text-xs text-gray-500">
          At Semi-Auto level, actions below this amount are auto-approved.
        </p>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">$</span>
          <input
            type="number"
            value={activeConfig.spendLimit}
            onChange={(e) =>
              setLocalConfig({
                ...activeConfig,
                spendLimit: parseFloat(e.target.value) || 0,
              })
            }
            className="w-32 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            min={0}
            step={10}
          />
          <span className="text-sm text-gray-500">USD</span>
        </div>
      </div>

      {/* Per-Agent Overrides */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-2 text-sm font-medium text-gray-700">
          Per-Agent Overrides
        </h3>
        <p className="mb-3 text-xs text-gray-500">
          Override the default autonomy level for specific agent types.
        </p>
        <div className="max-h-96 space-y-2 overflow-y-auto">
          {AGENT_TYPES.map((agentType) => {
            const agentLevel =
              activeConfig.agentLevels[agentType] ?? activeConfig.defaultLevel;
            return (
              <div
                key={agentType}
                className="flex items-center justify-between rounded-md border border-gray-100 p-2"
              >
                <span className="text-sm text-gray-700">{agentType}</span>
                <div className="flex gap-1">
                  {([0, 1, 2] as const).map((level) => (
                    <button
                      key={level}
                      onClick={() => setAgentLevel(agentType, level)}
                      className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                        agentLevel === level
                          ? AUTONOMY_LEVEL_COLORS[level]
                          : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                      }`}
                    >
                      {AUTONOMY_LEVEL_LABELS[level]}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
