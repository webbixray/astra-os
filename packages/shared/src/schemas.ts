import { z } from 'zod';

export const OrganizationSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
  plan_tier: z.enum(['free', 'starter', 'professional', 'business', 'enterprise']),
  settings: z.record(z.unknown()).default({}),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(255),
  avatar_url: z.string().url().nullable(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export const TeamMemberSchema = z.object({
  id: z.string().uuid(),
  organization_id: z.string().uuid(),
  user_id: z.string().uuid(),
  role: z.enum(['owner', 'admin', 'member', 'viewer']),
  permissions: z.array(z.string()).default([]),
  joined_at: z.string().datetime(),
});

export const CampaignSchema = z.object({
  id: z.string().uuid(),
  organization_id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string().nullable(),
  status: z.enum(['draft', 'pending_approval', 'active', 'paused', 'completed', 'archived']),
  budget_amount: z.number().positive().nullable(),
  budget_currency: z.string().length(3).default('USD'),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  channels: z.array(z.string()).default([]),
  objective: z.string().nullable(),
  created_by: z.string().uuid(),
  ai_generated: z.boolean().default(false),
  metadata: z.record(z.unknown()).default({}),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export const ContentSchema = z.object({
  id: z.string().uuid(),
  campaign_id: z.string().uuid().nullable(),
  organization_id: z.string().uuid(),
  title: z.string().min(1).max(500),
  content_type: z.enum(['blog', 'social', 'email', 'ad', 'landing', 'video_desc']),
  body: z.string(),
  status: z.enum(['draft', 'review', 'approved', 'published', 'archived']),
  brand_profile_id: z.string().uuid().nullable(),
  generated_by_ai: z.boolean().default(false),
  version: z.number().int().positive().default(1),
  scheduled_at: z.string().datetime().nullable(),
  published_at: z.string().datetime().nullable(),
  created_by: z.string().uuid(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export const PaginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});

export const CreateOrganizationSchema = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
});

export const CreateCampaignSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  budget_amount: z.number().positive().optional(),
  budget_currency: z.string().length(3).default('USD'),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  channels: z.array(z.string()).default([]),
  objective: z.string().optional(),
});

export const UpdateCampaignSchema = CreateCampaignSchema.partial();
