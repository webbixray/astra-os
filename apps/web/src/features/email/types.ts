export interface EmailProvider {
  id: string;
  name: string;
  provider_type: string;
  from_email: string;
  from_name: string;
  is_verified: boolean;
  is_active: boolean;
}

export interface EmailCampaign {
  id: string;
  name: string;
  subject: string;
  body?: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'partially_sent' | 'failed';
  recipient_count: number;
  sent_count: number;
  open_count: number;
  click_count: number;
  bounce_count: number;
  from_email?: string;
  from_name?: string;
  scheduled_at: string | null;
  sent_at: string | null;
  created_at: string;
  events?: EmailEvent[];
}

export interface EmailEvent {
  id: string;
  event_type: string;
  recipient_email: string;
  occurred_at: string;
}

export interface EmailAnalytics {
  total_campaigns: number;
  total_sent: number;
  total_opens: number;
  total_clicks: number;
  total_bounces: number;
  avg_open_rate: number;
  avg_click_rate: number;
  avg_bounce_rate: number;
}

export const PROVIDER_TYPES = ['sendgrid', 'ses', 'smtp'] as const;
