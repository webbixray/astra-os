'use client';

import Link from 'next/link';
import { Plus, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useContentList } from '@/features/content/api/useContent';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import { SkeletonCard } from '@/components/ui/skeleton';
import { CONTENT_STATUS_COLORS } from '@/lib/constants';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const statusColors = CONTENT_STATUS_COLORS;

export default function ContentPage() {
  const { orgId } = useOrg();
  const { data: contents, isLoading } = useContentList(orgId);

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Content Studio</h1>
          <p className="text-sm text-muted-foreground">
            Create and manage marketing content
          </p>
        </div>
        <Link href="/content/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Content
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : contents && contents.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {contents.map((content) => (
            <Link key={content.id} href={`/content/${content.id}`}>
              <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm transition-colors hover:bg-accent/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <h3 className="font-medium leading-none">{content.title}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">{content.content_type}</p>
                  </div>
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      statusColors[content.status],
                    )}
                  >
                    {content.status}
                  </span>
                </div>
                <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                  {content.body || 'No content yet'}
                </p>
                <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>v{content.version}</span>
                  {content.generated_by_ai && <span>AI generated</span>}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <FileText className="h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">No content yet</p>
          <p className="text-sm text-muted-foreground">
            Create your first piece of content
          </p>
          <Link href="/content/new">
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              Create Content
            </Button>
          </Link>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
