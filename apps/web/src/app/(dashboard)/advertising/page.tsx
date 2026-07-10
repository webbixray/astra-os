'use client';

import { useState } from 'react';
import { Plus, RefreshCw, Unlink, Globe, Image, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAdAccounts, useConnectAccount, useSyncAccount, useDisconnectAccount } from '@/features/advertising/api/useAdvertising';
import { useOrg } from '@/lib/org';
import Link from 'next/link';
import { SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const PLATFORM_MAP: Record<string, string> = {
  google: 'Google Ads',
  meta: 'Meta Ads',
  linkedin: 'LinkedIn Ads',
  tiktok: 'TikTok Ads',
};

const PLATFORM_COLORS: Record<string, string> = {
  google: 'text-blue-500',
  meta: 'text-blue-600',
  linkedin: 'text-sky-600',
  tiktok: 'text-pink-500',
};

export default function AdvertisingPage() {
  const { orgId } = useOrg();
  const { data: accounts, isLoading } = useAdAccounts(orgId);
  const connectMutation = useConnectAccount();
  const syncMutation = useSyncAccount();
  const disconnectMutation = useDisconnectAccount();

  const [showConnect, setShowConnect] = useState(false);
  const [form, setForm] = useState({ platform: 'google', account_name: '', platform_account_id: '' });

  const handleConnect = async () => {
    await connectMutation.mutateAsync({
      organization_id: orgId,
      ...form,
    });
    setShowConnect(false);
    setForm({ platform: 'google', account_name: '', platform_account_id: '' });
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Ad Accounts</h1>
          <p className="text-sm text-muted-foreground">Connect and manage your ad platforms</p>
        </div>
        <div className="flex gap-2">
          <Link href="/advertising/creatives">
            <Button variant="outline">
              <Image className="mr-2 h-4 w-4" />
              Creatives
            </Button>
          </Link>
          <Button onClick={() => setShowConnect(!showConnect)}>
            <Plus className="mr-2 h-4 w-4" />
            Connect Account
          </Button>
        </div>
      </div>

      {showConnect && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-col gap-4">
            <Select
              value={form.platform}
              onChange={(e) => setForm({ ...form, platform: e.target.value })}
              options={[
                { value: 'google', label: 'Google Ads' },
                { value: 'meta', label: 'Meta Ads' },
                { value: 'linkedin', label: 'LinkedIn Ads' },
                { value: 'tiktok', label: 'TikTok Ads' },
              ]}
            />
            <Input
              placeholder="Account Name"
              aria-label="Account name"
              value={form.account_name}
              onChange={(e) => setForm({ ...form, account_name: e.target.value })}
            />
            <Input
              placeholder="Platform Account ID"
              aria-label="Platform account ID"
              value={form.platform_account_id}
              onChange={(e) => setForm({ ...form, platform_account_id: e.target.value })}
            />
            <div className="flex gap-2">
              <Button onClick={handleConnect} disabled={connectMutation.isPending}>
                Connect
              </Button>
              <Button variant="ghost" onClick={() => setShowConnect(false)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : accounts && accounts.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {accounts.map((account) => (
            <div key={account.id} className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <Globe className={`h-5 w-5 ${PLATFORM_COLORS[account.platform] || 'text-muted-foreground'}`} />
                  <div>
                    <h3 className="font-medium">{account.account_name}</h3>
                    <p className="text-sm text-muted-foreground">{PLATFORM_MAP[account.platform] || account.platform}</p>
                  </div>
                </div>
                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-500/10 text-green-500">
                  {account.status}
                </span>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => syncMutation.mutate(account.id)}
                  disabled={syncMutation.isPending}
                >
                  <RefreshCw className={`mr-1 h-3 w-3 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                  Sync
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-500 hover:text-red-600"
                  onClick={() => disconnectMutation.mutate(account.id)}
                >
                  <Unlink className="mr-1 h-3 w-3" />
                  Disconnect
                </Button>
                <Link href={`/advertising/${account.id}`} className="ml-auto">
                  <Button size="sm" variant="ghost">
                    Campaigns <ChevronRight className="ml-1 h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Globe className="h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">No ad accounts connected</p>
          <p className="text-sm text-muted-foreground">Connect Google, Meta, LinkedIn, or TikTok to get started</p>
          <Button onClick={() => setShowConnect(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Connect Account
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
