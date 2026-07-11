'use client';

import { useState } from 'react';
import {
  TrendingUp,
  Target,
  BarChart3,
  Download,
  Calendar,
  Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useAnalyticsOverview,
  useCampaignPerformance,
  useAdPerformance,
} from '@/features/analytics/api/useAnalytics';
import { useReportTrends } from '@/features/reports/api/useReports';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import Link from 'next/link';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const TABS = [
  { key: 'overview', label: 'Overview', icon: BarChart3 },
  { key: 'campaigns', label: 'Campaigns', icon: Target },
  { key: 'ads', label: 'Platform Ads', icon: Layers },
  { key: 'trends', label: 'Trends', icon: TrendingUp },
];

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-muted',
  active: 'bg-green-500',
  paused: 'bg-yellow-500',
  completed: 'bg-blue-500',
  archived: 'bg-muted-foreground',
};

export default function AnalyticsPage() {
  const [tab, setTab] = useState('overview');
  const { orgId } = useOrg();
  const { data: overview } = useAnalyticsOverview(orgId);
  const { data: campaignPerf } = useCampaignPerformance(orgId);
  const { data: adPerf } = useAdPerformance();
  const { data: trends } = useReportTrends(orgId, 'spend', 30);

  const handleExport = (type: string) => {
    const params = new URLSearchParams({ type, organization_id: orgId });
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/reports/export/csv?${params}`,
      '_blank', 'noopener',
    );
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-semibold">Analytics & Reports</h1>
            <p className="text-sm text-muted-foreground">
              Campaign and advertising performance
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handleExport('campaigns')}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Link href="/analytics/scheduled">
            <Button variant="outline" size="sm">
              <Calendar className="mr-2 h-4 w-4" />
              Scheduled Reports
            </Button>
          </Link>
        </div>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              'flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              tab === t.key
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="space-y-6">
          {overview ? (
            <div className="grid grid-cols-4 gap-4">
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm text-muted-foreground">Total Campaigns</p>
                <p className="mt-1 text-2xl font-semibold">{overview.total_campaigns}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm text-muted-foreground">Active Campaigns</p>
                <p className="mt-1 text-2xl font-semibold">{overview.active_campaigns}</p>
                <p className="text-xs text-muted-foreground">{overview.draft_campaigns} in draft</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm text-muted-foreground">Content Pieces</p>
                <p className="mt-1 text-2xl font-semibold">{overview.total_content}</p>
                <p className="text-xs text-muted-foreground">{overview.published_content} published</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm text-muted-foreground">Total Budget</p>
                <p className="mt-1 text-2xl font-semibold">
                  ${overview.total_budget.toLocaleString()}
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="rounded-lg border bg-card p-4">
                  <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                  <div className="mt-2 h-7 w-20 animate-pulse rounded bg-muted" />
                </div>
              ))}
            </div>
          )}

          <div className="rounded-lg border bg-card p-4">
            <h2 className="mb-3 text-sm font-medium">Campaign Status Breakdown</h2>
            {overview ? (
              <div className="flex gap-1">
                {Object.entries(overview.status_breakdown).map(([status, count]) => (
                  <div key={status} className="flex flex-1 flex-col items-center gap-1">
                    <div className="flex h-20 w-full items-end">
                      <div
                        className={cn(
                          'w-full rounded-t',
                          STATUS_COLORS[status] || 'bg-muted',
                        )}
                        style={{
                          height: `${Math.max(
                            5,
                            (count / overview.total_campaigns) * 100,
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{status}</span>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-20 items-end gap-1">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex-1 animate-pulse rounded-t bg-muted" style={{ height: `${20 + i * 15}%` }} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'campaigns' && (
        <div className="rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h2 className="text-sm font-medium">Campaign Performance</h2>
            <Button size="sm" variant="ghost" onClick={() => handleExport('campaigns')}>
              <Download className="mr-1 h-3 w-3" /> CSV
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Budget</th>
                  <th className="px-4 py-3 font-medium">Spend</th>
                  <th className="px-4 py-3 font-medium">Impressions</th>
                  <th className="px-4 py-3 font-medium">Clicks</th>
                  <th className="px-4 py-3 font-medium">Conversions</th>
                  <th className="px-4 py-3 font-medium">Revenue</th>
                  <th className="px-4 py-3 font-medium">ROI</th>
                </tr>
              </thead>
              <tbody>
                {campaignPerf ? campaignPerf.map((c) => (
                  <tr key={c.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="px-4 py-3 font-medium">{c.name}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
                        {c.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">${c.budget.toLocaleString()}</td>
                    <td className="px-4 py-3">${c.spend.toLocaleString()}</td>
                    <td className="px-4 py-3">{c.impressions.toLocaleString()}</td>
                    <td className="px-4 py-3">{c.clicks.toLocaleString()}</td>
                    <td className="px-4 py-3">{c.conversions}</td>
                    <td className="px-4 py-3">${c.revenue.toLocaleString()}</td>
                    <td className="px-4 py-3 font-medium text-green-500">
                      {c.roi > 0 ? '+' : ''}{c.roi}%
                    </td>
                  </tr>
                )) : [1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="border-b last:border-0">
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 w-full animate-pulse rounded bg-muted" /></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'ads' && (
        <div className="space-y-6">
          {adPerf ? (
            <>
              <div className="grid grid-cols-4 gap-4">
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Impressions</p>
                  <p className="mt-1 text-2xl font-semibold">{adPerf.total_impressions.toLocaleString()}</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Clicks</p>
                  <p className="mt-1 text-2xl font-semibold">{adPerf.total_clicks.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">CTR: {adPerf.ctr.toFixed(2)}%</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Conversions</p>
                  <p className="mt-1 text-2xl font-semibold">{adPerf.total_conversions}</p>
                  <p className="text-xs text-muted-foreground">Rate: {adPerf.conversion_rate.toFixed(2)}%</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">ROI</p>
                  <p className="mt-1 text-2xl font-semibold">{adPerf.roi.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">Spent: ${adPerf.total_spend.toLocaleString()}</p>
                </div>
              </div>

              {adPerf.platforms.map((platform) => (
                <div key={platform.name} className="rounded-lg border bg-card">
                  <div className="border-b px-4 py-3">
                    <h3 className="text-sm font-medium capitalize">{platform.name}</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-xs text-muted-foreground">
                          <th className="px-4 py-3 font-medium">Campaign</th>
                          <th className="px-4 py-3 font-medium">Spend</th>
                          <th className="px-4 py-3 font-medium">Impressions</th>
                          <th className="px-4 py-3 font-medium">Clicks</th>
                          <th className="px-4 py-3 font-medium">Conversions</th>
                          <th className="px-4 py-3 font-medium">Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {platform.campaigns.map((c) => (
                          <tr key={c.id} className="border-b last:border-0 hover:bg-muted/50">
                            <td className="px-4 py-3 font-medium">{c.name}</td>
                            <td className="px-4 py-3">${c.spend.toLocaleString()}</td>
                            <td className="px-4 py-3">{c.impressions.toLocaleString()}</td>
                            <td className="px-4 py-3">{c.clicks.toLocaleString()}</td>
                            <td className="px-4 py-3">{c.conversions}</td>
                            <td className="px-4 py-3">${c.revenue.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <>
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="rounded-lg border bg-card p-4">
                    <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                    <div className="mt-2 h-7 w-20 animate-pulse rounded bg-muted" />
                  </div>
                ))}
              </div>
              {[1, 2].map((i) => (
                <div key={i} className="rounded-lg border bg-card p-4">
                  <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                  <div className="mt-3 space-y-2">
                    {[1, 2, 3].map((j) => (
                      <div key={j} className="h-4 w-full animate-pulse rounded bg-muted" />
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {tab === 'trends' && (
        <div className="space-y-6">
          {trends ? (
            <>
              <div className="grid grid-cols-4 gap-4">
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Total Spend (30d)</p>
                  <p className="mt-1 text-2xl font-semibold">${trends.total.toLocaleString()}</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Daily Average</p>
                  <p className="mt-1 text-2xl font-semibold">${trends.average.toLocaleString()}</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Peak Day</p>
                  <p className="mt-1 text-2xl font-semibold">${trends.peak.toLocaleString()}</p>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <p className="text-sm text-muted-foreground">Metric</p>
                  <p className="mt-1 text-lg font-semibold capitalize">{trends.metric}</p>
                </div>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <h2 className="mb-3 text-sm font-medium">Daily {trends.metric} Trend (30 days)</h2>
                <div className="flex h-40 items-end gap-0.5">
                  {trends.daily.map((d: { date: string; value: number }, i: number) => {
                    const maxVal = trends.peak || 1;
                    const h = Math.max(3, (d.value / maxVal) * 100);
                    return (
                      <div
                        key={i}
                        className="flex flex-1 flex-col items-center"
                        title={`${d.date}: $${d.value}`}
                      >
                        <div
                          className="w-full rounded-t bg-primary transition-all hover:bg-primary/80"
                          style={{ height: `${h}%` }}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="rounded-lg border bg-card p-4">
                    <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                    <div className="mt-2 h-7 w-20 animate-pulse rounded bg-muted" />
                  </div>
                ))}
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="h-4 w-48 animate-pulse rounded bg-muted" />
                <div className="mt-3 flex h-40 items-end gap-0.5">
                  {Array.from({ length: 30 }).map((_, i) => (
                    <div key={i} className="flex flex-1 items-end">
                      <div className="w-full animate-pulse rounded-t bg-muted" style={{ height: `${10 + Math.random() * 80}%` }} />
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
