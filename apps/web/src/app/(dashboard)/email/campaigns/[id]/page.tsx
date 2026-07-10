'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Mail, TrendingUp, MousePointerClick, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEmailCampaign } from '@/features/email/api/useEmail';
import { cn } from '@/lib/utils';
import { SkeletonTitle } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export default function EmailCampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: campaign, isLoading } = useEmailCampaign(id);

  if (isLoading) {
    return (
      <ErrorBoundary>
      <div className="p-6">
        <SkeletonTitle />
      </div>
      </ErrorBoundary>
    );
  }

  if (!campaign) {
    return (
      <ErrorBoundary>
      <div className="p-6">
        <p className="text-muted-foreground">Campaign not found</p>
        <Button variant="outline" onClick={() => router.push('/email/campaigns')} className="mt-4">
          Back
        </Button>
      </div>
      </ErrorBoundary>
    );
  }

  const openRate = campaign.sent_count > 0 ? (campaign.open_count / campaign.sent_count) * 100 : 0;
  const clickRate = campaign.sent_count > 0 ? (campaign.click_count / campaign.sent_count) * 100 : 0;

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <Button variant="ghost" onClick={() => router.push('/email/campaigns')} className="-ml-3">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to campaigns
      </Button>

      <div>
        <h1 className="text-2xl font-semibold">{campaign.name}</h1>
        <p className="text-sm text-muted-foreground mt-1">{campaign.subject}</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Mail className="h-4 w-4" />
            Sent
          </div>
          <p className="mt-1 text-2xl font-bold">{campaign.sent_count.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            Open Rate
          </div>
          <p className="mt-1 text-2xl font-bold">{openRate.toFixed(1)}%</p>
          <p className="text-xs text-muted-foreground">{campaign.open_count} opens</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <MousePointerClick className="h-4 w-4" />
            Click Rate
          </div>
          <p className="mt-1 text-2xl font-bold">{clickRate.toFixed(1)}%</p>
          <p className="text-xs text-muted-foreground">{campaign.click_count} clicks</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AlertTriangle className="h-4 w-4" />
            Bounces
          </div>
          <p className="mt-1 text-2xl font-bold">{campaign.bounce_count}</p>
        </div>
      </div>

      {campaign.events && campaign.events.length > 0 && (
        <div className="rounded-lg border bg-card">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-medium">Recent Events</h3>
          </div>
          <div className="divide-y max-h-64 overflow-y-auto">
            {campaign.events.slice(0, 50).map((event) => (
              <div key={event.id} className="flex items-center gap-3 px-4 py-2 text-sm">
                <span className={cn(
                  'h-2 w-2 rounded-full',
                  event.event_type === 'sent' ? 'bg-blue-500' :
                  event.event_type === 'opened' ? 'bg-green-500' :
                  event.event_type === 'clicked' ? 'bg-yellow-500' :
                  'bg-red-500',
                )} />
                <span className="capitalize">{event.event_type}</span>
                <span className="text-xs text-muted-foreground">{event.recipient_email}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {new Date(event.occurred_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!campaign.events?.length && (
        <div className="flex flex-col items-center py-12 text-center text-muted-foreground">
          <Mail className="mb-2 h-8 w-8" />
          <p className="text-sm">No events recorded yet</p>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
