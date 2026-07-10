'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  TrendingUp,
  Users,
  Banknote,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { BudgetSection } from './budget-section';
import { ABTestSection } from './ab-test-section';
import { useCampaign, useUpdateCampaign } from '@/features/campaigns/api/useCampaigns';
import {
  useCampaignBudget,
  useSetCampaignBudget,
  useRecordSpend,
} from '@/features/campaigns/api/useAdvancedCampaigns';
import {
  useABTests,
  useCreateABTest,
  useAddVariant,
  useStartABTest,
  useDetermineWinner,
} from '@/features/campaigns/api/useAdvancedCampaigns';
import { cn } from '@/lib/utils';
import { Skeleton, SkeletonTitle } from '@/components/ui/skeleton';
import { CAMPAIGN_STATUS_COLORS } from '@/lib/constants';

const statusColors = CAMPAIGN_STATUS_COLORS;

const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['pending_approval', 'archived'],
  pending_approval: ['active', 'draft', 'archived'],
  active: ['paused', 'completed', 'archived'],
  paused: ['active', 'completed', 'archived'],
  completed: ['archived'],
  archived: [],
};

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: campaign, isLoading, isError, error } = useCampaign(id);
  const updateCampaign = useUpdateCampaign(id);

  const { data: budget, isLoading: budgetLoading } = useCampaignBudget(id);
  const setBudget = useSetCampaignBudget(id);
  const recordSpend = useRecordSpend(id);

  const { data: abTests, isLoading: abLoading } = useABTests(id);
  const createABTest = useCreateABTest(id);
  const [newTestId, setNewTestId] = useState<string | null>(null);
  const addVariant = useAddVariant(newTestId || '');
  const startABTest = useStartABTest();
  const determineWinner = useDetermineWinner();

  const [budgetAmount, setBudgetAmount] = useState('');
  const [threshold, setThreshold] = useState('80');
  const [spendAmount, setSpendAmount] = useState('');
  const [showNewTest, setShowNewTest] = useState(false);
  const [testName, setTestName] = useState('');
  const [testMetric, setTestMetric] = useState('conversion_rate');
  const [variantName, setVariantName] = useState('');
  const [variantTraffic, setVariantTraffic] = useState('50');
  const [activeTestDetail, setActiveTestDetail] = useState<string | null>(null);

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Failed to load campaign'}
          </p>
          <Button variant="outline" onClick={() => router.push('/campaigns')}>
            Back to campaigns
          </Button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl p-6 space-y-8">
        <SkeletonTitle />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-40 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Campaign not found</p>
        <Button variant="outline" onClick={() => router.push('/campaigns')} className="mt-4">
          Back to campaigns
        </Button>
      </div>
    );
  }

  const handleTransition = async (status: string) => {
    await updateCampaign.mutateAsync({ status });
  };

  const transitions = STATUS_TRANSITIONS[campaign.status] || [];

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-5xl p-6 space-y-8">
      <Button variant="ghost" onClick={() => router.push('/campaigns')} className="-ml-3">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to campaigns
      </Button>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{campaign.name}</h1>
            <span className={cn(
              'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusColors[campaign.status],
            )}>
              {campaign.status.replace('_', ' ')}
            </span>
          </div>
          {campaign.description && (
            <p className="mt-2 text-muted-foreground">{campaign.description}</p>
          )}
        </div>
        {transitions.length > 0 && (
          <div className="flex gap-2">
            {transitions.map((s) => (
              <Button
                key={s}
                variant="outline"
                size="sm"
                onClick={() => handleTransition(s)}
                disabled={updateCampaign.isPending}
              >
                {s === 'active' ? 'Launch' : s.replace('_', ' ')}
              </Button>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-3 text-sm font-medium text-muted-foreground">Channels</h3>
          <div className="flex flex-wrap gap-2">
            {campaign.channels.length > 0
              ? campaign.channels.map((ch) => (
                  <span key={ch} className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium">
                    {ch}
                  </span>
                ))
              : <span className="text-sm text-muted-foreground">None selected</span>}
          </div>
        </div>
        {campaign.objective && (
          <div className="rounded-lg border bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-muted-foreground">Objective</h3>
            <p className="text-sm capitalize">{campaign.objective}</p>
          </div>
        )}
        {campaign.start_date && (
          <div className="rounded-lg border bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-muted-foreground">Dates</h3>
            <p className="text-sm">
              {campaign.start_date} {campaign.end_date ? `→ ${campaign.end_date}` : ''}
            </p>
          </div>
        )}
      </div>

      <BudgetSection
        budget={budget}
        isLoading={budgetLoading}
        budgetAmount={budgetAmount}
        onBudgetAmountChange={setBudgetAmount}
        threshold={threshold}
        onThresholdChange={setThreshold}
        spendAmount={spendAmount}
        onSpendAmountChange={setSpendAmount}
        setBudget={setBudget}
        recordSpend={recordSpend}
      />

      <ABTestSection
        abTests={abTests}
        isLoading={abLoading}
        showNewTest={showNewTest}
        onToggleNewTest={() => setShowNewTest(!showNewTest)}
        testName={testName}
        onTestNameChange={setTestName}
        testMetric={testMetric}
        onTestMetricChange={setTestMetric}
        variantName={variantName}
        onVariantNameChange={setVariantName}
        variantTraffic={variantTraffic}
        onVariantTrafficChange={setVariantTraffic}
        activeTestDetail={activeTestDetail}
        onToggleTestDetail={(id) => setActiveTestDetail(activeTestDetail === id ? null : id)}
        createABTest={createABTest}
        addVariant={addVariant}
        startABTest={startABTest}
        determineWinner={determineWinner}
      />

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">Quick Stats</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm">Status: <strong>{campaign.status.replace('_', ' ')}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-500" />
              <span className="text-sm">Channels: <strong>{campaign.channels.length || 0}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <Banknote className="h-4 w-4 text-yellow-500" />
              <span className="text-sm">Budget: <strong>{campaign.budget_amount ? `${campaign.budget_currency} ${campaign.budget_amount.toLocaleString()}` : 'Not set'}</strong></span>
            </div>
          </div>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">A/B Test Activity</h3>
          {abLoading ? (
            <Skeleton className="h-12" />
          ) : abTests && abTests.length > 0 ? (
            <div className="space-y-2">
              {abTests.slice(0, 3).map((t) => (
                <div key={t.id} className="flex items-center justify-between text-sm">
                  <span className="truncate">{t.name}</span>
                  <span className={cn(
                    'text-xs',
                    t.status === 'running' ? 'text-green-500' :
                    t.status === 'completed' ? 'text-blue-500' : 'text-muted-foreground',
                  )}>
                    {t.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No active tests</p>
          )}
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
