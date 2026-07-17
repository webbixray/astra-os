'use client';

import { useState } from 'react';
import { Beaker, Plus, Play, Trophy, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface ABTest {
  id: string;
  name: string;
  status: string;
  goal_metric: string;
  variants_count: number;
  winner_variant_id: string | null;
  created_at: string;
}

interface ABTestSectionProps {
  abTests: ABTest[] | undefined;
  isLoading: boolean;
  showNewTest: boolean;
  onToggleNewTest: () => void;
  testName: string;
  onTestNameChange: (v: string) => void;
  testMetric: string;
  onTestMetricChange: (v: string) => void;
  variantName: string;
  onVariantNameChange: (v: string) => void;
  variantTraffic: string;
  onVariantTrafficChange: (v: string) => void;
  activeTestDetail: string | null;
  onToggleTestDetail: (id: string) => void;
  createABTest: { mutateAsync: (data: { name: string; goal_metric: string }) => Promise<{ id: string }>; isPending: boolean };
  addVariant: { mutateAsync: (data: { name: string; traffic_percent: number }) => Promise<unknown> };
  startABTest: { mutate: (id: string) => void };
  determineWinner: { mutate: (id: string) => void };
}

const GOAL_METRICS = ['ctr', 'conversion_rate', 'cpa', 'clicks', 'conversions'] as const;

export function ABTestSection({
  abTests,
  isLoading,
  showNewTest,
  onToggleNewTest,
  testName,
  onTestNameChange,
  testMetric,
  onTestMetricChange,
  variantName,
  onVariantNameChange,
  variantTraffic,
  onVariantTrafficChange,
  activeTestDetail,
  onToggleTestDetail,
  createABTest,
  addVariant,
  startABTest,
  determineWinner,
}: ABTestSectionProps) {
  const [_newTestId, setNewTestId] = useState<string | null>(null);

  return (
    <section className="rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Beaker className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-medium">A/B Tests</h2>
        </div>
        <Button size="sm" variant="outline" onClick={onToggleNewTest}>
          <Plus className="mr-1 h-3 w-3" />
          New Test
        </Button>
      </div>

      {showNewTest && (
        <div className="border-b p-4 space-y-3 bg-accent/20">
          <label htmlFor="ab-test-name" className="text-xs font-medium text-muted-foreground">Test name</label>
          <Input
            id="ab-test-name"
            placeholder="Test name"
            value={testName}
            onChange={(e) => onTestNameChange(e.target.value)}
          />
          <label htmlFor="ab-test-metric" className="text-xs font-medium text-muted-foreground">Goal metric</label>
          <Select
            id="ab-test-metric"
            value={testMetric}
            onChange={(e) => onTestMetricChange(e.target.value)}
            options={GOAL_METRICS.map((m) => ({ value: m, label: m.replace('_', ' ') }))}
          />
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label htmlFor="variant-name" className="text-xs font-medium text-muted-foreground">Variant name</label>
              <Input
                id="variant-name"
                placeholder="Variant A name"
                value={variantName}
                onChange={(e) => onVariantNameChange(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="variant-traffic" className="text-xs font-medium text-muted-foreground">Traffic %</label>
              <Input
                id="variant-traffic"
                type="number"
                placeholder="Traffic %"
                value={variantTraffic}
                onChange={(e) => onVariantTrafficChange(e.target.value)}
                className="w-20"
              />
            </div>
            <Button
              size="sm"
              disabled={createABTest.isPending || !testName || !variantName}
              onClick={async () => {
                const res = await createABTest.mutateAsync({ name: testName, goal_metric: testMetric });
                setNewTestId(res.id);
                await addVariant.mutateAsync({
                  name: variantName,
                  traffic_percent: parseFloat(variantTraffic) || 50,
                });
                setNewTestId(null);
                onToggleNewTest();
                onTestNameChange('');
                onVariantNameChange('');
                onVariantTrafficChange('50');
              }}
            >
              {createABTest.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
              Create
            </Button>
          </div>
        </div>
      )}

      <div className="divide-y">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />
            Loading tests...
          </div>
        ) : abTests && abTests.length > 0 ? (
          abTests.map((t) => (
            <div key={t.id} className="px-4 py-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{t.name}</span>
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-medium',
                    t.status === 'running' ? 'bg-green-500/10 text-green-500' :
                    t.status === 'completed' ? 'bg-blue-500/10 text-blue-500' :
                    'bg-muted text-muted-foreground',
                  )}>
                    {t.status}
                  </span>
                  {t.winner_variant_id && <Trophy className="h-3 w-3 text-yellow-500" />}
                </div>
                <div className="flex gap-1">
                  {t.status === 'draft' && (
                    <Button size="sm" variant="ghost" className="h-7 text-xs"
                      onClick={() => startABTest.mutate(t.id)}>
                      <Play className="mr-1 h-3 w-3" /> Start
                    </Button>
                  )}
                  {t.status === 'running' && (
                    <Button size="sm" variant="ghost" className="h-7 text-xs"
                      onClick={() => determineWinner.mutate(t.id)}>
                      <Trophy className="mr-1 h-3 w-3" /> Determine Winner
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs"
                    onClick={() => onToggleTestDetail(t.id)}
                  >
                    {activeTestDetail === t.id ? 'Hide' : 'Details'}
                  </Button>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Goal: {t.goal_metric.replace('_', ' ')} · {t.variants_count} variant{t.variants_count !== 1 ? 's' : ''} · {new Date(t.created_at).toLocaleDateString()}
              </p>
            </div>
          ))
        ) : (
          <div className="p-8 text-center text-sm text-muted-foreground">
            <Beaker className="mx-auto mb-2 h-5 w-5" />
            No A/B tests yet
          </div>
        )}
      </div>
    </section>
  );
}
