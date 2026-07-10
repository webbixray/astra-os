import type {
  CAMPAIGN_STATUSES,
  CONTENT_TYPES,
  CONTENT_STATUSES,
  AD_PLATFORMS,
  WORKFLOW_NODE_TYPES,
  ORGANIZATION_ROLES,
  PLAN_TIERS,
  AGENT_TYPES,
  MEMORY_TYPES,
} from './constants';

export type CampaignStatus = (typeof CAMPAIGN_STATUSES)[number];
export type ContentType = (typeof CONTENT_TYPES)[number];
export type ContentStatus = (typeof CONTENT_STATUSES)[number];
export type AdPlatform = (typeof AD_PLATFORMS)[number];
export type WorkflowNodeType = (typeof WORKFLOW_NODE_TYPES)[number];
export type OrganizationRole = (typeof ORGANIZATION_ROLES)[number];
export type PlanTier = (typeof PLAN_TIERS)[number];
export type AgentType = (typeof AGENT_TYPES)[number];
export type MemoryType = (typeof MEMORY_TYPES)[number];

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
