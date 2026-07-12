/** Governance feature types — approval, autonomy, audit. */

export interface ApprovalRule {
  id: string;
  name: string;
  description?: string;
  trigger: string;
  is_active: boolean;
  priority: number;
  conditions: Record<string, unknown>;
  approver_roles: string[];
  approval_timeout_hours: number;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRequest {
  id: string;
  action_type: string;
  action_summary: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired' | 'delegated' | 'cancelled';
  assigned_role: string;
  timeout_at: string | null;
  created_at: string;
}

export interface ApprovalDecision {
  id: string;
  request_id: string;
  action: string;
  reason: string;
}

export interface AutonomyConfig {
  id: string;
  organization_id: string;
  default_level: number;
  agent_levels: Record<string, number>;
  action_overrides: Record<string, number>;
  auto_approve_spend_limit: number;
  auto_approve_currency: string;
  auto_execute_channels: string[];
}

export interface AgentAction {
  id: string;
  agent_type: string;
  agent_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  success: boolean;
  was_auto_executed: boolean;
  autonomy_level: number;
  reasoning: string;
  reasoning_trace: Array<{
    step: number;
    thought: string;
    action: string;
    result: string;
  }>;
  tokens_used: number;
  cost_usd: number;
  model_used: string;
  created_at: string;
}

export interface ActionExplanation {
  action_id: string;
  one_line: string;
  paragraph: string;
  detailed: string;
  reasoning_steps: Array<{
    step: number;
    thought: string;
    action: string;
    result: string;
  }>;
  autonomy_context: {
    level: number;
    was_auto_executed: boolean;
    had_approval_request: boolean;
  };
  outcome: {
    success: boolean;
    error: string;
  };
}

export interface AuditSummary {
  organization_id: string;
  total_actions: number;
  successful: number;
  failed: number;
  auto_executed: number;
  human_approved: number;
  total_cost_usd: number;
  total_tokens: number;
  by_agent_type: Record<string, number>;
  by_action: Record<string, number>;
  by_autonomy_level: Record<string, number>;
}

export const AUTONOMY_LEVEL_LABELS: Record<number, string> = {
  0: 'Advisory',
  1: 'Semi-Auto',
  2: 'Full Auto',
};

export const AUTONOMY_LEVEL_COLORS: Record<number, string> = {
  0: 'bg-yellow-100 text-yellow-800',
  1: 'bg-blue-100 text-blue-800',
  2: 'bg-green-100 text-green-800',
};

export const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  expired: 'bg-gray-100 text-gray-600',
  delegated: 'bg-purple-100 text-purple-800',
  cancelled: 'bg-gray-100 text-gray-600',
};
