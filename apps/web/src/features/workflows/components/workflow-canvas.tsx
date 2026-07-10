'use client';

import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { WorkflowNode, WorkflowEdge } from '../types';
import { NODE_COLORS, NODE_ICONS } from '../types';

interface WorkflowCanvasProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  onAddNode?: (type: WorkflowNode['type']) => void;
  onRemoveNode?: (id: string) => void;
  readOnly?: boolean;
}

const NODE_TYPES = ['trigger', 'action', 'condition', 'delay', 'approval', 'end'] as const;

export function WorkflowCanvas({ nodes, edges, onAddNode, onRemoveNode, readOnly = false }: WorkflowCanvasProps) {
  return (
    <div className="flex gap-6">
      {!readOnly && (
        <div className="w-48 shrink-0 space-y-2 rounded-lg border bg-card p-4">
          <h3 className="mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Nodes</h3>
          {NODE_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => onAddNode?.(type)}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent',
                NODE_COLORS[type],
                'border-l-2',
              )}
            >
              <span>{NODE_ICONS[type]}</span>
              <span className="capitalize">{type}</span>
            </button>
          ))}
        </div>
      )}

      <div className="relative min-h-[400px] flex-1 rounded-lg border bg-card/50 p-8">
        {nodes.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            {readOnly ? 'No nodes in this workflow' : 'Drag nodes from the palette to build your workflow'}
          </div>
        ) : (
          <svg className="absolute inset-0 h-full w-full pointer-events-none">
            {edges.map((edge) => {
              const source = nodes.find((n) => n.id === edge.source_id);
              const target = nodes.find((n) => n.id === edge.target_id);
              if (!source || !target) return null;
              return (
                <line
                  key={edge.id}
                  x1={source.position_x + 80}
                  y1={source.position_y + 24}
                  x2={target.position_x + 80}
                  y2={target.position_y}
                  className="stroke-muted-foreground/30"
                  strokeWidth={2}
                  strokeDasharray="6 3"
                />
              );
            })}
          </svg>
        )}

        <div className="relative space-y-6">
          {nodes.map((node) => (
            <div
              key={node.id}
              className={cn(
                'relative flex items-center gap-3 rounded-lg border-2 px-4 py-3',
                NODE_COLORS[node.type],
              )}
              style={{
                marginLeft: `${node.position_x}px`,
                transform: `translateY(${node.position_y}px)`,
              }}
            >
              <span className="text-lg">{NODE_ICONS[node.type]}</span>
              <div className="flex-1">
                <p className="text-sm font-medium">{node.label}</p>
                <p className="text-xs text-muted-foreground capitalize">{node.type}</p>
              </div>
              {!readOnly && onRemoveNode && (
                <button
                  onClick={() => onRemoveNode(node.id)}
                  className="rounded p-1 text-muted-foreground hover:bg-background/50 hover:text-foreground"
                  aria-label="Remove node"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
