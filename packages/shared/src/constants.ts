export const CAMPAIGN_STATUSES = [
  'draft',
  'pending_approval',
  'active',
  'paused',
  'completed',
  'archived',
] as const;

export const CONTENT_TYPES = [
  'blog',
  'social',
  'email',
  'ad',
  'landing',
  'video_desc',
] as const;

export const CONTENT_STATUSES = [
  'draft',
  'review',
  'approved',
  'published',
  'archived',
] as const;

export const AD_PLATFORMS = [
  'google',
  'meta',
  'linkedin',
  'twitter',
  'tiktok',
] as const;

export const WORKFLOW_NODE_TYPES = [
  'trigger:schedule',
  'trigger:webhook',
  'trigger:event',
  'trigger:manual',
  'action:http_request',
  'action:ai_generate',
  'action:ai_classify',
  'action:ai_extract',
  'action:send_email',
  'action:slack_message',
  'action:create_campaign',
  'action:create_content',
  'action:create_ad',
  'action:database_query',
  'action:code',
  'logic:condition',
  'logic:switch',
  'logic:loop',
  'logic:delay',
  'logic:wait_for_event',
  'human:approval',
  'human:review',
  'human:input',
  'output:return',
  'output:log',
  'output:notification',
] as const;

export const ORGANIZATION_ROLES = [
  'owner',
  'admin',
  'member',
  'viewer',
] as const;

export const PLAN_TIERS = [
  'free',
  'starter',
  'professional',
  'business',
  'enterprise',
] as const;

export const AGENT_TYPES = [
  'ceo',
  'marketing_director',
  'creative_director',
  'advertising_director',
  'research_director',
  'analytics_director',
  'workflow_director',
  'compliance_director',
  'memory_manager',
  'content_specialist',
  'seo_specialist',
  'social_media_specialist',
  'copywriter',
  'designer',
  'brand_voice',
  'campaign_optimizer',
  'bid_manager',
  'audience_researcher',
  'market_researcher',
  'competitor_analyst',
  'trend_analyzer',
  'data_analyst',
  'attribution_modeler',
  'report_generator',
  'workflow_builder',
  'automation_scheduler',
  'integration_manager',
  'content_reviewer',
  'privacy_auditor',
  'policy_enforcer',
  'knowledge_graph_operator',
  'brand_memory_curator',
  'performance_historian',
] as const;

export const MEMORY_TYPES = [
  'brand',
  'campaign',
  'customer',
  'knowledge',
  'semantic',
  'workflow',
] as const;
