'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Globe,
  Send,
  Clock,
  CheckCircle2,
  RotateCcw,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SkeletonLine } from '@/components/ui/skeleton';
import { usePublishingQueue, useRetryPublish, useCancelPublish } from '@/features/content/api/useContentPublishing';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';

const PLATFORM_ICONS: Record<string, string> = {
  website: '🌐',
  twitter: '🐦',
  linkedin: '💼',
  facebook: '📘',
  instagram: '📷',
  email: '📧',
};

const STATUS_TABS = ['all', 'scheduled', 'publishing', 'published', 'failed'] as const;

export default function PublishingQueuePage() {
  const { orgId } = useOrg();
  const [status, setStatus] = useState<string>('all');
  const { data: queue, isLoading, isError, error, refetch } = usePublishingQueue(orgId, status === 'all' ? undefined : status);
  const retryPublish = useRetryPublish();
  const cancelPublish = useCancelPublish();

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Publishing Queue</h1>
          <p className="text-sm text-muted-foreground">
            Monitor and manage content publishing across platforms
          </p>
        </div>
        <Link href="/content">
          <Button variant="outline" size="sm">
            <Send className="mr-2 h-4 w-4" />
            Content Library
          </Button>
        </Link>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {STATUS_TABS.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={cn(
              'cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              status === s
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            )}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isError ? (
        <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Failed to load publishing queue'}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Try Again
          </Button>
        </div>
      ) : isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 rounded-lg border bg-card p-4">
              <SkeletonLine className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-2">
                <SkeletonLine className="h-4 w-1/4" />
                <SkeletonLine className="h-3 w-1/3" />
              </div>
              <SkeletonLine className="h-7 w-16 rounded-md" />
            </div>
          ))}
        </div>
      ) : queue && queue.length > 0 ? (
        <div className="rounded-lg border divide-y">
          {queue.map((entry) => (
            <div key={entry.id} className="flex items-start gap-4 px-4 py-3 hover:bg-accent/30 transition-colors">
              <span className="mt-1 text-lg">
                {PLATFORM_ICONS[entry.platform] || '📬'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium capitalize">{entry.platform}</span>
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-medium',
                    entry.status === 'published' ? 'bg-green-500/10 text-green-500' :
                    entry.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                    entry.status === 'publishing' ? 'bg-yellow-500/10 text-yellow-500' :
                    'bg-muted text-muted-foreground',
                  )}>
                    {entry.status}
                  </span>
                  {entry.external_url && (
                    <a
                      href={entry.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-500 hover:underline flex items-center gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View
                    </a>
                  )}
                </div>
                <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>Content: {entry.content_id.slice(0, 8)}...</span>
                  {entry.scheduled_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(entry.scheduled_at).toLocaleDateString(undefined, {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </span>
                  )}
                  {entry.published_at && (
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      {new Date(entry.published_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                {entry.error_message && (
                  <p className="mt-1 text-xs text-red-500">{entry.error_message}</p>
                )}
              </div>
              <div className="flex gap-1 shrink-0">
                {entry.status === 'failed' && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => retryPublish.mutate(entry.id)}
                    disabled={retryPublish.isPending}
                  >
                    <RotateCcw className="mr-1 h-3 w-3" />
                    Retry
                  </Button>
                )}
                {(entry.status === 'scheduled' || entry.status === 'publishing') && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs text-red-500 hover:text-red-500"
                    onClick={() => cancelPublish.mutate(entry.id)}
                    disabled={cancelPublish.isPending}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Globe className="h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No publishing activity</p>
          <p className="text-sm text-muted-foreground">
            Publish or schedule content to see it here
          </p>
          <Link href="/content">
            <Button variant="outline">
              <Send className="mr-2 h-4 w-4" />
              Go to Content
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
