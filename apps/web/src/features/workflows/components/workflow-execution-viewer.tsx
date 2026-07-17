'use client';

import { cn } from '@/lib/utils';
import { EXECUTION_STATUS_COLORS } from '../types';
import type { WorkflowNode, ExecutionStep } from '../types';
import { CheckCircle2, XCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface WorkflowExecutionViewerProps {
  nodes: WorkflowNode[];
  steps: ExecutionStep[];
  executionStatus: string;
  error?: string | null;
}

const STEP_STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4 text-muted-foreground" />,
  running: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  skipped: <AlertCircle className="h-4 w-4 text-muted-foreground" />,
  waiting_approval: <Clock className="h-4 w-4 text-yellow-500" />,
};

export function WorkflowExecutionViewer({
  nodes,
  steps,
  executionStatus,
  error,
}: WorkflowExecutionViewerProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-sm font-medium">Execution Status</h3>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
            EXECUTION_STATUS_COLORS[executionStatus] || 'bg-muted text-muted-foreground',
          )}
        >
          {executionStatus}
        </span>
        {error && (
          <span className="text-xs text-destructive">{error}</span>
        )}
      </div>

      <div className="relative space-y-1">
        {steps.map((step, i) => {
          const node = nodes.find((n) => n.id === step.node_id);
          const nodeType = node?.type || 'action';
          const nodeLabel = node?.label || step.node_id;

          return (
            <div
              key={step.id}
              className={cn(
                'flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors',
                step.status === 'completed' && 'border-green-500/20 bg-green-500/5',
                step.status === 'failed' && 'border-red-500/20 bg-red-500/5',
                step.status === 'running' && 'border-blue-500/20 bg-blue-500/5',
                step.status === 'pending' && 'border-border',
                step.status === 'waiting_approval' && 'border-yellow-500/20 bg-yellow-500/5',
              )}
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-background">
                {STEP_STATUS_ICONS[step.status]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{nodeLabel}</span>
                  <span className="text-xs text-muted-foreground capitalize">{nodeType}</span>
                </div>
                {step.error && (
                  <p className="mt-1 text-xs text-destructive truncate">{step.error}</p>
                )}
                {step.result && step.status === 'completed' && (
                  <p className="mt-1 text-xs text-muted-foreground truncate">
                    {String(step.result.step || step.result.status || 'Done')}
                  </p>
                )}
              </div>
              <div className="text-xs text-muted-foreground">
                {i + 1}/{steps.length}
              </div>
            </div>
          );
        })}

        {steps.length === 0 && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No execution steps recorded
          </div>
        )}
      </div>
    </div>
  );
}
