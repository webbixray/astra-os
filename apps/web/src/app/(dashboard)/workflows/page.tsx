'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Workflow } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useWorkflows } from '@/features/workflows/api/useWorkflows';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import { SkeletonCard } from '@/components/ui/skeleton';
import { WORKFLOW_STATUS_COLORS } from '@/lib/constants';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const STATUSES = ['all', 'draft', 'active', 'paused', 'completed', 'archived'];
const statusColors = WORKFLOW_STATUS_COLORS;

export default function WorkflowsPage() {
  const [status, setStatus] = useState('all');
  const { orgId } = useOrg();
  const { data: workflows, isLoading } = useWorkflows(orgId, status === 'all' ? undefined : status);

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Workflows</h1>
          <p className="text-sm text-muted-foreground">
            Automate marketing processes and approvals
          </p>
        </div>
        <Link href="/workflows/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Workflow
          </Button>
        </Link>
      </div>

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

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : workflows && workflows.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows.map((wf) => (
            <Link key={wf.id} href={`/workflows/${wf.id}`}>
              <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm transition-colors hover:bg-accent/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Workflow className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-medium leading-none">{wf.name}</h3>
                  </div>
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      statusColors[wf.status],
                    )}
                  >
                    {wf.status}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-1">{wf.description || 'No description'}</p>
                <p className="mt-3 text-xs text-muted-foreground">{wf.nodes.length} nodes, {wf.edges.length} connections</p>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Workflow className="h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">No workflows yet</p>
          <p className="text-sm text-muted-foreground">Create automated marketing processes</p>
          <Link href="/workflows/new">
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              Create Workflow
            </Button>
          </Link>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
