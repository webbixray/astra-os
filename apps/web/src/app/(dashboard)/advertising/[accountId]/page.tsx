'use client';

import { useParams } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Plus, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAdCampaigns, useCreateAdCampaign } from '@/features/advertising/api/useAdvertising';
import { useOrg } from '@/lib/org';
import Link from 'next/link';
import { useState } from 'react';
import { SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const statusColors: Record<string, string> = {
  draft: 'bg-muted text-muted-foreground',
  active: 'bg-green-500/10 text-green-500',
  paused: 'bg-yellow-500/10 text-yellow-500',
  completed: 'bg-blue-500/10 text-blue-500',
  archived: 'bg-muted text-muted-foreground',
};

const objectiveLabels: Record<string, string> = {
  awareness: 'Awareness',
  consideration: 'Consideration',
  conversion: 'Conversion',
};

export default function AccountCampaignsPage() {
  const params = useParams();
  const accountId = params.accountId as string;
  const { orgId } = useOrg();
  const { data: campaigns, isLoading } = useAdCampaigns(orgId);
  const createMutation = useCreateAdCampaign();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [objective, setObjective] = useState('awareness');

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      organization_id: orgId,
      ad_account_id: accountId,
      name,
      objective,
    });
    setShowCreate(false);
    setName('');
    setObjective('awareness');
  };

  const accountCampaigns = campaigns?.filter((c) => c.ad_account_id === accountId) || [];

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/advertising">
            <Button variant="ghost" size="icon" aria-label="Back">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Campaigns</h1>
            <p className="text-sm text-muted-foreground">Ad campaigns for this account</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" />
          New Campaign
        </Button>
      </div>

      {showCreate && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-col gap-4">
            <Input
              placeholder="Campaign Name"
              aria-label="Campaign name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              options={[
                { value: 'awareness', label: 'Awareness' },
                { value: 'consideration', label: 'Consideration' },
                { value: 'conversion', label: 'Conversion' },
              ]}
            />
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name || createMutation.isPending}>
                Create
              </Button>
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : accountCampaigns.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accountCampaigns.map((campaign) => (
            <div key={campaign.id} className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{campaign.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {objectiveLabels[campaign.objective] || campaign.objective}
                  </p>
                </div>
                <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', statusColors[campaign.status] || 'bg-muted text-muted-foreground')}>
                  {campaign.status}
                </span>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                {campaign.daily_budget > 0 && <span>${campaign.daily_budget}/day</span>}
                <span className={campaign.sync_status === 'synced' ? 'text-green-500' : 'text-yellow-500'}>
                  {campaign.sync_status === 'synced' ? 'Synced' : 'Not synced'}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <p className="text-lg text-muted-foreground">No campaigns yet</p>
          <p className="text-sm text-muted-foreground">Create your first ad campaign</p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Campaign
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
