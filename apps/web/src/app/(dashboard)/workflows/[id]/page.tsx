'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Play, Workflow } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useWorkflow, useUpdateWorkflow, useExecuteWorkflow } from '@/features/workflows/api/useWorkflows';
import { WorkflowCanvas } from '@/features/workflows/components/workflow-canvas';
import { cn } from '@/lib/utils';
import { SkeletonTitle } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import type { WorkflowNode } from '@/features/workflows/types';

const statusColors: Record<string, string> = {
  draft: 'bg-muted text-muted-foreground',
  active: 'bg-green-500/10 text-green-500',
  paused: 'bg-blue-500/10 text-blue-500',
  completed: 'bg-muted text-muted-foreground',
  archived: 'bg-muted text-muted-foreground',
};

const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['active', 'archived'],
  active: ['paused', 'completed', 'archived'],
  paused: ['active', 'archived'],
  completed: ['archived'],
  archived: [],
};

export default function WorkflowDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: workflow, isLoading } = useWorkflow(id);
  const updateWorkflow = useUpdateWorkflow(id);
  const executeWorkflow = useExecuteWorkflow();

  const handleTransition = async (status: string) => {
    await updateWorkflow.mutateAsync({ status } as Partial<import('@/features/workflows/types').Workflow>);
  };

  const handleAddNode = async (type: WorkflowNode['type']) => {
    if (!workflow) return;
    const newId = `${type}-${Date.now()}`;
    const newNode: WorkflowNode = {
      id: newId,
      type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
      config: {},
      position_x: 0,
      position_y: workflow.nodes.length * 80,
    };
    const newEdge = {
      id: `e-${workflow.nodes[workflow.nodes.length - 1]?.id || 'start'}-${newId}`,
      source_id: workflow.nodes[workflow.nodes.length - 1]?.id || 'trigger-1',
      target_id: newId,
      label: '',
    };
    await updateWorkflow.mutateAsync({
      nodes: [...workflow.nodes, newNode],
      edges: [...workflow.edges, newEdge],
    } as unknown as Partial<import('@/features/workflows/types').Workflow>);
  };

  const handleRemoveNode = async (nodeId: string) => {
    if (!workflow) return;
    await updateWorkflow.mutateAsync({
      nodes: workflow.nodes.filter((n) => n.id !== nodeId),
      edges: workflow.edges.filter((e) => e.source_id !== nodeId && e.target_id !== nodeId),
    } as unknown as Partial<import('@/features/workflows/types').Workflow>);
  };

  const handleExecute = async () => {
    if (!workflow) return;
    await executeWorkflow.mutateAsync({
      workflowId: workflow.id,
      orgId: workflow.organization_id,
    });
  };

  if (isLoading) {
    return (
      <ErrorBoundary>
      <div className="p-6">
        <SkeletonTitle />
      </div>
      </ErrorBoundary>
    );
  }

  if (!workflow) {
    return (
      <ErrorBoundary>
      <div className="p-6">
        <p className="text-muted-foreground">Workflow not found</p>
        <Button variant="outline" onClick={() => router.push('/workflows')} className="mt-4">
          Back to workflows
        </Button>
      </div>
      </ErrorBoundary>
    );
  }

  const transitions = STATUS_TRANSITIONS[workflow.status] || [];

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <Button variant="ghost" onClick={() => router.push('/workflows')} className="-ml-3 w-fit">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to workflows
      </Button>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Workflow className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-2xl font-semibold">{workflow.name}</h1>
            <span className={cn(
              'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusColors[workflow.status],
            )}>
              {workflow.status}
            </span>
          </div>
          {workflow.description && (
            <p className="mt-1 text-sm text-muted-foreground">{workflow.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          {transitions.includes('active') && (
            <Button size="sm" onClick={handleExecute} disabled={executeWorkflow.isPending}>
              <Play className="mr-1 h-3 w-3" />
              Run
            </Button>
          )}
          {transitions.map((status) => (
            <Button
              key={status}
              variant="outline"
              size="sm"
              onClick={() => handleTransition(status)}
              disabled={updateWorkflow.isPending}
            >
              {status}
            </Button>
          ))}
        </div>
      </div>

      {(executeWorkflow.data as { status?: string } | undefined) && (
        <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3 text-sm">
          Execution started: {(executeWorkflow.data as { status: string }).status}
        </div>
      )}

      <WorkflowCanvas
        nodes={workflow.nodes}
        edges={workflow.edges}
        onAddNode={handleAddNode}
        onRemoveNode={handleRemoveNode}
        readOnly={workflow.status !== 'draft'}
      />
    </div>
    </ErrorBoundary>
  );
}
