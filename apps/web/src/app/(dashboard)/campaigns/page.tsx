'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { Plus, Target, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { CampaignCard } from '@/features/campaigns/components/campaign-card';
import { useCampaigns } from '@/features/campaigns/api/useCampaigns';
import { useCampaignOverview } from '@/features/calendar/api/useCalendar';
import { useOrg } from '@/lib/org';
import { SkeletonCard } from '@/components/ui/skeleton';

const CampaignsTemplatesTab = dynamic(
  () => import('./campaigns-templates-tab').then((m) => ({ default: m.CampaignsTemplatesTab })),
  { ssr: false },
);

const STATUSES = ['all', 'draft', 'pending_approval', 'active', 'paused', 'completed', 'archived'];

export default function CampaignsPage() {
  const [status, setStatus] = useState<string>('all');
  const [tab, setTab] = useState<'campaigns' | 'templates'>('campaigns');
  const { orgId } = useOrg();
  const { data: campaigns, isLoading, isError: campaignsError, refetch: refetchCampaigns } = useCampaigns(orgId, status === 'all' ? undefined : status);
  const { data: overview } = useCampaignOverview(orgId);

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Manage your marketing campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border bg-card p-0.5">
            <button
              onClick={() => setTab('campaigns')}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === 'campaigns' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              }`}
            >
              Campaigns
            </button>
            <button
              onClick={() => setTab('templates')}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === 'templates' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              }`}
            >
              Templates
            </button>
          </div>
          {tab === 'campaigns' ? (
            <Link href="/campaigns/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Campaign
              </Button>
            </Link>
          ) : null}
        </div>
      </div>

      {tab === 'campaigns' ? (
        <>
          {overview ? (
            <div className="grid grid-cols-4 gap-4">
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Target className="h-4 w-4" />
                  Campaigns
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.total_campaigns}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Globe className="h-4 w-4" />
                  Ad Campaigns
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.total_ad_campaigns}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Target className="h-4 w-4" />
                  Combined
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.combined_total}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Globe className="h-4 w-4" />
                  Platforms
                </div>
                <p className="mt-1 text-2xl font-semibold">
                  {Object.keys(overview.ad_platform_breakdown || {}).length}
                </p>
                <p className="text-xs text-muted-foreground">
                  {Object.entries(overview.ad_platform_breakdown || {}).map(([p, c]) => `${p}: ${c}`).join(', ')}
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="rounded-lg border bg-card p-4">
                  <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                  <div className="mt-2 h-7 w-16 animate-pulse rounded bg-muted" />
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2 border-b pb-2">
            {STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  status === s
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>

          {campaignsError ? (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
              <p className="text-sm text-destructive">Failed to load campaigns</p>
              <Button variant="outline" size="sm" onClick={() => refetchCampaigns()}>
                Try Again
              </Button>
            </div>
          ) : isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : campaigns && campaigns.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {campaigns.map((campaign) => (
                <Link key={campaign.id} href={`/campaigns/${campaign.id}`}>
                  <CampaignCard campaign={campaign} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <p className="text-lg text-muted-foreground">No campaigns yet</p>
              <p className="text-sm text-muted-foreground">
                Create your first campaign to get started
              </p>
              <Link href="/campaigns/new">
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Campaign
                </Button>
              </Link>
            </div>
          )}
        </>
      ) : (
        <Suspense fallback={<SkeletonCard />}>
          <CampaignsTemplatesTab orgId={orgId} />
        </Suspense>
      )}
    </div>
    </ErrorBoundary>
  );
}
