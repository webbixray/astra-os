export interface WorkflowNode {
  id: string;
  type: 'trigger' | 'action' | 'condition' | 'delay' | 'approval' | 'end';
  label: string;
  config: Record<string, unknown>;
  position_x: number;
  position_y: number;
}

export interface WorkflowEdge {
  id: string;
  source_id: string;
  target_id: string;
  label: string;
}

export interface Workflow {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'archived';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type CreateWorkflowInput = {
  organization_id: string;
  name: string;
  description?: string;
};

export interface WorkflowExecution {
  id: string;
  status: string;
  steps: unknown[];
  error: string | null;
  created_at: string;
}

const NODE_COLORS: Record<string, string> = {
  trigger: 'border-emerald-500 bg-emerald-500/10',
  action: 'border-blue-500 bg-blue-500/10',
  condition: 'border-amber-500 bg-amber-500/10',
  delay: 'border-purple-500 bg-purple-500/10',
  approval: 'border-rose-500 bg-rose-500/10',
  end: 'border-muted bg-muted/50',
};

const NODE_ICONS: Record<string, string> = {
  trigger: '▶',
  action: '⚡',
  condition: '◇',
  delay: '⏱',
  approval: '✓',
  end: '●',
};

export { NODE_COLORS, NODE_ICONS };
