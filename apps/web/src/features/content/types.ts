export interface Content {
  id: string;
  campaign_id: string | null;
  organization_id: string;
  title: string;
  content_type: string;
  body: string;
  status: 'draft' | 'review' | 'approved' | 'published' | 'archived';
  brand_profile_id: string | null;
  generated_by_ai: boolean;
  version: number;
  scheduled_at: string | null;
  published_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type CreateContentInput = {
  organization_id: string;
  title: string;
  content_type?: string;
  campaign_id?: string;
  body?: string;
  brand_profile_id?: string;
};

export interface ContentPublishEntry {
  id: string;
  content_id: string;
  platform: string;
  status: 'scheduled' | 'publishing' | 'published' | 'failed';
  scheduled_at: string | null;
  published_at: string | null;
  external_url: string | null;
  error_message: string | null;
  created_at: string;
}

export const PUBLISH_PLATFORMS = [
  'website',
  'twitter',
  'linkedin',
  'facebook',
  'instagram',
  'email',
] as const;
