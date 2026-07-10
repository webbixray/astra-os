'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Send, Clock, Globe, Loader2, RotateCcw, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useContent, useUpdateContent } from '@/features/content/api/useContent';
import {
  usePublishingHistory,
  usePublishContent,
  useScheduleContent,
  useRetryPublish,
  useCancelPublish,
} from '@/features/content/api/useContentPublishing';
import { PUBLISH_PLATFORMS } from '@/features/content/types';
import { cn } from '@/lib/utils';
import { SkeletonTitle, SkeletonLine, SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const statusColors: Record<string, string> = {
  draft: 'bg-muted text-muted-foreground',
  review: 'bg-yellow-500/10 text-yellow-500',
  approved: 'bg-green-500/10 text-green-500',
  published: 'bg-blue-500/10 text-blue-500',
  archived: 'bg-muted text-muted-foreground',
};

const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['review', 'archived'],
  review: ['approved', 'draft', 'archived'],
  approved: ['published', 'draft', 'archived'],
  published: ['archived'],
  archived: [],
};

const PLATFORM_ICONS: Record<string, string> = {
  website: '🌐',
  twitter: '🐦',
  linkedin: '💼',
  facebook: '📘',
  instagram: '📷',
  email: '📧',
};

export default function ContentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: content, isLoading, isError, error } = useContent(id);
  const updateContent = useUpdateContent(id);
  const { data: publishingHistory } = usePublishingHistory(id);
  const publishContent = usePublishContent();
  const scheduleContent = useScheduleContent();
  const retryPublish = useRetryPublish();
  const cancelPublish = useCancelPublish();

  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl p-6 space-y-8">
        <SkeletonLine className="h-9 w-24" />
        <div className="space-y-3">
          <SkeletonTitle className="w-96" />
          <SkeletonLine className="h-4 w-48" />
        </div>
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Failed to load content'}
          </p>
          <Button variant="outline" onClick={() => router.push('/content')}>
            Back to content
          </Button>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <div className="flex flex-col items-center gap-4 rounded-lg border py-16 text-center">
          <p className="text-muted-foreground">Content not found</p>
          <Button variant="outline" onClick={() => router.push('/content')}>
            Back to content
          </Button>
        </div>
      </div>
    );
  }

  const handleTransition = async (status: string) => {
    await updateContent.mutateAsync({ status });
  };

  const transitions = STATUS_TRANSITIONS[content.status] || [];
  const isPublishable = content.status === 'approved';

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-5xl p-6 space-y-8">
      <Button variant="ghost" onClick={() => router.push('/content')} className="-ml-3">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to content
      </Button>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{content.title}</h1>
            <span className={cn(
              'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusColors[content.status],
            )}>
              {content.status}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
            <span>{content.content_type}</span>
            <span>v{content.version}</span>
            {content.generated_by_ai && <span>AI generated</span>}
          </div>
        </div>
        {transitions.length > 0 && (
          <div className="flex gap-2">
            {transitions.map((s) => (
              <Button
                key={s}
                variant="outline"
                size="sm"
                onClick={() => handleTransition(s)}
                disabled={updateContent.isPending}
              >
                {s === 'published' ? 'Publish' : s.replace('_', ' ')}
              </Button>
            ))}
          </div>
        )}
      </div>

      {content.body && (
        <div className="rounded-lg border bg-card p-6">
          <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
            {content.body}
          </div>
        </div>
      )}

      <section className="rounded-lg border bg-card">
        <div className="flex items-center gap-2 border-b px-4 py-3">
          <Send className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-medium">Publish</h2>
        </div>
        <div className="p-4 space-y-4">
          {!isPublishable && content.status !== 'published' && (
            <p className="text-xs text-muted-foreground bg-accent/50 rounded px-3 py-2">
              Content must be in <strong>approved</strong> status before publishing.
            </p>
          )}

          <div className="flex flex-wrap gap-2">
            {PUBLISH_PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => setSelectedPlatform(p === selectedPlatform ? '' : p)}
                disabled={!isPublishable && content.status !== 'published'}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors',
                  selectedPlatform === p
                    ? 'border-primary bg-accent'
                    : 'hover:bg-accent',
                  !isPublishable && content.status !== 'published' && 'opacity-50 cursor-not-allowed',
                )}
              >
                <span>{PLATFORM_ICONS[p] || '📬'}</span>
                <span className="capitalize">{p}</span>
              </button>
            ))}
          </div>

          {selectedPlatform && (
            <div className="flex flex-wrap items-center gap-3 border-t pt-4">
                <Input
                  type="datetime-local"
                  value={scheduleDate ? `${scheduleDate}T${scheduleTime}` : ''}
                  onChange={(e) => {
                    const [d, t] = (e.target.value || '').split('T');
                    setScheduleDate(d || '');
                    setScheduleTime(t || '');
                  }}
                />
              <Button
                size="sm"
                disabled={publishContent.isPending}
                onClick={() => {
                  if (scheduleDate && scheduleTime) {
                    scheduleContent.mutate({
                      content_id: id,
                      platform: selectedPlatform,
                      scheduled_at: `${scheduleDate}T${scheduleTime}:00`,
                    });
                  } else {
                    publishContent.mutate({ content_id: id, platform: selectedPlatform });
                  }
                  setSelectedPlatform('');
                  setScheduleDate('');
                  setScheduleTime('');
                }}
              >
                {publishContent.isPending ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : scheduleDate ? (
                  <Clock className="mr-1 h-3 w-3" />
                ) : (
                  <Send className="mr-1 h-3 w-3" />
                )}
                {scheduleDate ? 'Schedule' : 'Publish Now'}
              </Button>
            </div>
          )}
        </div>
      </section>

      <section className="rounded-lg border bg-card">
        <div className="flex items-center gap-2 border-b px-4 py-3">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-medium">Publishing History</h2>
        </div>
        {publishingHistory && publishingHistory.length > 0 ? (
          <div className="divide-y">
            {publishingHistory.map((entry) => (
              <div key={entry.id} className="px-4 py-3 flex items-start gap-3">
                <span className="mt-0.5 text-base">
                  {PLATFORM_ICONS[entry.platform] || '📬'}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
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
                    <span className="text-xs text-muted-foreground ml-auto">
                      {entry.published_at
                        ? new Date(entry.published_at).toLocaleDateString()
                        : entry.scheduled_at
                          ? `Scheduled: ${new Date(entry.scheduled_at).toLocaleDateString()}`
                          : new Date(entry.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {entry.error_message && (
                    <p className="mt-1 text-xs text-red-500">{entry.error_message}</p>
                  )}
                </div>
                <div className="flex gap-1 shrink-0">
                  {entry.status === 'failed' && (
                    <Button
                      size="sm"
                      variant="ghost"
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
                      variant="ghost"
                      className="h-7 text-xs text-red-500"
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
          <div className="p-8 text-center text-sm text-muted-foreground">
            <Globe className="mx-auto mb-2 h-5 w-5" />
            No publishing activity yet
          </div>
        )}
      </section>
    </div>
    </ErrorBoundary>
  );
}
