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

// --- Template types ---

export interface WorkflowTemplateSummary {
  template_id: string;
  name: string;
  description: string;
  category: string;
  node_count: number;
  edge_count: number;
  estimated_duration_minutes: number;
  tags: string[];
}

export interface WorkflowTemplateDetail extends WorkflowTemplateSummary {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface InstantiateTemplateInput {
  organization_id: string;
  name?: string;
  customizations?: Record<string, unknown>;
}

export interface InstantiatedWorkflow {
  workflow_id: string;
  template_id: string;
  name: string;
  description: string;
  node_count: number;
  edge_count: number;
  organization_id: string;
  created_by: string;
}

// --- Execution types ---

export interface ExecutionStep {
  id: string;
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'waiting_approval';
  result: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface WorkflowExecutionDetail {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  steps: ExecutionStep[];
  error: string | null;
  created_at: string;
  updated_at: string;
}

// --- Template category colors ---

export const TEMPLATE_CATEGORY_COLORS: Record<string, string> = {
  campaign: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  content: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  optimization: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  compliance: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
};

export const EXECUTION_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-muted text-muted-foreground',
  running: 'bg-blue-500/10 text-blue-500',
  paused: 'bg-yellow-500/10 text-yellow-500',
  completed: 'bg-green-500/10 text-green-500',
  failed: 'bg-red-500/10 text-red-500',
};
