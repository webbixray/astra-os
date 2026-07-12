'use client';

import { useState } from 'react';
import {
  useMinePatterns,
  useTransferSuggestions,
  useLearningInsights,
} from '../api/useKnowledge';
import {
  PATTERN_TYPE_LABELS,
  PRIORITY_COLORS,
  type CampaignPattern,
  type TransferRecommendation,
  type LearningInsight,
} from '../types';

interface KnowledgeGraphProps {
  organizationId: string;
}

export function KnowledgeGraph({ organizationId }: KnowledgeGraphProps) {
  const [activeView, setActiveView] = useState<'patterns' | 'transfers' | 'insights'>('patterns');

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Cross-Campaign Intelligence
      </h2>

      {/* View Tabs */}
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {[
          { key: 'patterns' as const, label: 'Patterns' },
          { key: 'transfers' as const, label: 'Transfer Learning' },
          { key: 'insights' as const, label: 'Insights' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveView(tab.key)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition ${
              activeView === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeView === 'patterns' && <PatternsView organizationId={organizationId} />}
      {activeView === 'transfers' && <TransfersView organizationId={organizationId} />}
      {activeView === 'insights' && <InsightsView organizationId={organizationId} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Patterns View
// ---------------------------------------------------------------------------

function PatternsView({ organizationId }: { organizationId: string }) {
  const mine = useMinePatterns(organizationId);
  const [patterns, setPatterns] = useState<CampaignPattern[]>([]);

  const handleMine = async () => {
    const data = await mine.mutateAsync({ limit: 20 });
    setPatterns(data.patterns);
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleMine}
        disabled={mine.isPending}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {mine.isPending ? 'Mining…' : 'Mine Patterns'}
      </button>

      {patterns.length > 0 && (
        <div className="space-y-3">
          {patterns.map((p) => (
            <div key={p.pattern_id} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800">
                  {PATTERN_TYPE_LABELS[p.pattern_type] || p.pattern_type}
                </span>
                <span className="text-sm font-medium text-gray-900">{p.title}</span>
              </div>
              <p className="mt-2 text-sm text-gray-600">{p.description}</p>
              <div className="mt-3 flex gap-4 text-xs text-gray-500">
                <span>Strength: {(p.strength * 100).toFixed(0)}%</span>
                <span>Confidence: {(p.confidence * 100).toFixed(0)}%</span>
                <span>{p.campaign_ids.length} campaign(s)</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Transfers View
// ---------------------------------------------------------------------------

function TransfersView({ organizationId }: { organizationId: string }) {
  const suggest = useTransferSuggestions(organizationId);
  const [recommendations, setRecommendations] = useState<TransferRecommendation[]>([]);
  const [targetId, setTargetId] = useState('');

  const handleSuggest = async () => {
    if (!targetId.trim()) return;
    const data = await suggest.mutateAsync({
      targetCampaignId: targetId.trim(),
      limit: 5,
    });
    setRecommendations(data.recommendations);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <input
          type="text"
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSuggest()}
          placeholder="Target campaign ID"
          className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
        <button
          onClick={handleSuggest}
          disabled={suggest.isPending || !targetId.trim()}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {suggest.isPending ? 'Finding…' : 'Suggest Transfers'}
        </button>
      </div>

      {recommendations.length > 0 && (
        <div className="space-y-3">
          {recommendations.map((r, i) => (
            <div key={i} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {r.source_campaign_name} → {r.target_campaign_name}
                  </p>
                  <p className="mt-0.5 text-xs text-gray-500">
                    Confidence: {(r.confidence * 100).toFixed(0)}% | {r.expected_lift}
                  </p>
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-600">{r.transfer_strategy}</p>
              {r.prerequisites.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-gray-500">Prerequisites:</p>
                  <ul className="mt-1 space-y-0.5 text-xs text-gray-500">
                    {r.prerequisites.map((p, j) => (
                      <li key={j}>• {p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Insights View
// ---------------------------------------------------------------------------

function InsightsView({ organizationId }: { organizationId: string }) {
  const { data, isLoading } = useLearningInsights(organizationId);
  const insights = data?.insights || [];

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading insights…</p>;
  }

  if (insights.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
        <p className="text-sm text-gray-500">
          No learning insights yet. Mine patterns to generate insights.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.map((insight) => (
        <div key={insight.insight_id} className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                PRIORITY_COLORS[insight.priority] || ''
              }`}
            >
              {insight.priority}
            </span>
            <span className="text-sm font-medium text-gray-900">{insight.title}</span>
          </div>
          <p className="mt-2 text-sm text-gray-600">{insight.description}</p>
          <div className="mt-3 flex gap-4 text-xs text-gray-500">
            <span>{insight.supporting_campaigns.length} campaign(s)</span>
            <span>Type: {insight.insight_type}</span>
          </div>
          {insight.recommended_actions.length > 0 && (
            <div className="mt-2">
              {insight.recommended_actions.map((action, i) => (
                <p key={i} className="text-xs text-blue-600">→ {action}</p>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
