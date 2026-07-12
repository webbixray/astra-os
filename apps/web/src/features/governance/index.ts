/** Governance feature — approval queue, autonomy settings, audit log. */

// Components
export { ApprovalQueue } from './components/approval-queue';
export { AutonomySettings } from './components/autonomy-settings';
export { AuditLogViewer } from './components/audit-log-viewer';

// API hooks
export {
  usePendingApprovals,
  useApprovalRules,
  useDecideApproval,
  useEvaluateRules,
} from './api/useApprovals';

export {
  useAutonomyConfig,
  useUpdateAutonomyConfig,
  useAgentActions,
  useActionExplanation,
  useAuditSummary,
} from './api/useAutonomy';

// Types
export type {
  ApprovalRule,
  ApprovalRequest,
  ApprovalDecision,
  AutonomyConfig,
  AgentAction,
  ActionExplanation,
  AuditSummary,
} from './types';

export {
  AUTONOMY_LEVEL_LABELS,
  AUTONOMY_LEVEL_COLORS,
  STATUS_COLORS,
} from './types';
