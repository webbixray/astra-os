'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Plus, Image, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import { useAdCreatives, useCreateAdCreative } from '@/features/advertising/api/useAdvertising';
import { useOrg } from '@/lib/org';
import Link from 'next/link';
import { SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const statusColors: Record<string, string> = {
  draft: 'bg-muted text-muted-foreground',
  approved: 'bg-green-500/10 text-green-500',
  rejected: 'bg-red-500/10 text-red-500',
  active: 'bg-blue-500/10 text-blue-500',
};

export default function CreativesPage() {
  const { orgId } = useOrg();
  const { data: creatives, isLoading } = useAdCreatives(orgId);
  const createMutation = useCreateAdCreative();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [type, setType] = useState('image');

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      organization_id: orgId,
      name,
      type,
    });
    setShowCreate(false);
    setName('');
    setType('image');
  };

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
            <h1 className="text-2xl font-semibold">Creative Library</h1>
            <p className="text-sm text-muted-foreground">Manage ad creatives and assets</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" />
          New Creative
        </Button>
      </div>

      {showCreate && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-col gap-4">
            <Input
              placeholder="Creative Name"
              aria-label="Creative name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Select
              value={type}
              onChange={(e) => setType(e.target.value)}
              options={[
                { value: 'image', label: 'Image' },
                { value: 'video', label: 'Video' },
                { value: 'carousel', label: 'Carousel' },
                { value: 'text', label: 'Text' },
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
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : creatives && creatives.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
          {creatives.map((creative) => (
            <div key={creative.id} className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
              <div className="flex items-center justify-center h-24 bg-muted rounded-md mb-3">
                <Image className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-sm">{creative.name}</h3>
                  <p className="text-xs text-muted-foreground">{creative.type}</p>
                </div>
                <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', statusColors[creative.status] || 'bg-muted text-muted-foreground')}>
                  {creative.status}
                </span>
              </div>
              {creative.headline && (
                <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{creative.headline}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Image className="h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">No creatives yet</p>
          <p className="text-sm text-muted-foreground">Create your first ad creative</p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Creative
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
