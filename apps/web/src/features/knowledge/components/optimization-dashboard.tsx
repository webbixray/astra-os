'use client';

import { useState } from 'react';
import {
  useBudgetOptimization,
  useCreativeFatigue,
  useAudienceExpansion,
} from '../api/useKnowledge';
import {
  type BudgetAllocation,
  type CreativeFatigueResult,
  type AudienceExpansionSuggestion,
} from '../types';

interface OptimizationDashboardProps {
  organizationId: string;
}

type Tab = 'budget' | 'fatigue' | 'audience';

export function OptimizationDashboard({ organizationId }: OptimizationDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('budget');

  const tabs: { key: Tab; label: string }[] = [
    { key: 'budget', label: 'Budget Optimization' },
    { key: 'fatigue', label: 'Creative Fatigue' },
    { key: 'audience', label: 'Audience Expansion' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Predictive Optimization
      </h2>

      {/* Tab Navigation */}
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition ${
              activeTab === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'budget' && <BudgetTab organizationId={organizationId} />}
      {activeTab === 'fatigue' && <FatigueTab organizationId={organizationId} />}
      {activeTab === 'audience' && <AudienceTab organizationId={organizationId} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Budget Tab
// ---------------------------------------------------------------------------

function BudgetTab({ organizationId }: { organizationId: string }) {
  const optimize = useBudgetOptimization(organizationId);
  const [allocations, setAllocations] = useState<BudgetAllocation[]>([]);

  const handleOptimize = async () => {
    // In production, campaign data would come from an API
    // Using placeholder data for demo
    const data = await optimize.mutateAsync({
      campaigns: [
        { id: '1', name: 'Summer Campaign', daily_budget: 100, roas: 4.5, impressions: 50000, clicks: 2500, conversions: 200, spend: 2000 },
        { id: '2', name: 'Brand Awareness', daily_budget: 150, roas: 1.8, impressions: 80000, clicks: 1600, conversions: 50, spend: 3000 },
        { id: '3', name: 'Retargeting', daily_budget: 80, roas: 6.2, impressions: 20000, clicks: 1400, conversions: 150, spend: 800 },
      ],
      totalBudget: 400,
    });
    setAllocations(data.allocations);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={handleOptimize}
          disabled={optimize.isPending}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {optimize.isPending ? 'Optimizing…' : 'Run Budget Optimization'}
        </button>
      </div>

      {allocations.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Campaign</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Current</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Suggested</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Change</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Rationale</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {allocations.map((a) => (
                <tr key={a.campaign_id}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{a.campaign_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600">${a.current_daily_budget}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">${a.suggested_daily_budget}</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`text-sm font-medium ${
                        a.budget_change_pct > 0 ? 'text-green-600' : a.budget_change_pct < 0 ? 'text-red-600' : 'text-gray-500'
                      }`}
                    >
                      {a.budget_change_pct > 0 ? '+' : ''}{a.budget_change_pct}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{a.rationale}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-500">{(a.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Fatigue Tab
// ---------------------------------------------------------------------------

function FatigueTab({ organizationId }: { organizationId: string }) {
  const detectFatigue = useCreativeFatigue(organizationId);
  const [results, setResults] = useState<CreativeFatigueResult[]>([]);
  const [fatiguedCount, setFatiguedCount] = useState(0);

  const handleDetect = async () => {
    const data = await detectFatigue.mutateAsync({
      creatives: [
        { id: 'c1', name: 'Summer Banner v1', ctr_history: [0.05, 0.048, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02], current_ctr: 0.02, peak_ctr: 0.05 },
        { id: 'c2', name: 'Retargeting Video', ctr_history: [0.03, 0.031, 0.032, 0.031, 0.033, 0.032, 0.031], current_ctr: 0.031, peak_ctr: 0.033 },
        { id: 'c3', name: 'Brand Story Carousel', ctr_history: [0.04, 0.038, 0.035, 0.032, 0.03], current_ctr: 0.03, peak_ctr: 0.04 },
      ],
    });
    setResults(data.results);
    setFatiguedCount(data.fatigued_count);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={handleDetect}
          disabled={detectFatigue.isPending}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {detectFatigue.isPending ? 'Analyzing…' : 'Detect Creative Fatigue'}
        </button>
        {fatiguedCount > 0 && (
          <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">
            {fatiguedCount} fatigued creative(s)
          </span>
        )}
      </div>

      {results.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {results.map((r) => (
            <div
              key={r.creative_id}
              className={`rounded-lg border p-4 ${
                r.is_fatigued
                  ? 'border-red-200 bg-red-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-900">{r.creative_name}</h3>
                {r.is_fatigued && (
                  <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                    Fatigued
                  </span>
                )}
              </div>
              <div className="mt-3 space-y-1 text-xs text-gray-600">
                <p>CTR: {(r.current_ctr * 100).toFixed(2)}% (peak: {(r.peak_ctr * 100).toFixed(2)}%)</p>
                <p>Days since peak: {r.days_since_peak}</p>
                <p>Decline rate: {r.decline_rate.toFixed(2)}%/day</p>
              </div>
              <p className="mt-3 text-xs text-gray-500">{r.recommendation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Audience Tab
// ---------------------------------------------------------------------------

function AudienceTab({ organizationId }: { organizationId: string }) {
  const expand = useAudienceExpansion(organizationId);
  const [suggestions, setSuggestions] = useState<AudienceExpansionSuggestion[]>([]);
  const [source, setSource] = useState('');

  const handleExpand = async () => {
    if (!source.trim()) return;
    const data = await expand.mutateAsync({
      sourceAudience: source.trim(),
      limit: 5,
    });
    setSuggestions(data.suggestions);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <input
          type="text"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleExpand()}
          placeholder="Source audience (e.g., 'tech professionals 25-45')"
          className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
        <button
          onClick={handleExpand}
          disabled={expand.isPending || !source.trim()}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {expand.isPending ? 'Analyzing…' : 'Suggest Expansions'}
        </button>
      </div>

      {suggestions.length > 0 && (
        <div className="space-y-3">
          {suggestions.map((s, i) => (
            <div
              key={i}
              className="rounded-lg border border-gray-200 bg-white p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    → {s.suggested_audience}
                  </p>
                  <p className="mt-0.5 text-xs text-gray-500">
                    Overlap: {(s.overlap_estimate * 100).toFixed(0)}% | Confidence: {(s.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-600">{s.rationale}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
