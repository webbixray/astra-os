export interface Campaign {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  status: 'draft' | 'pending_approval' | 'active' | 'paused' | 'completed' | 'archived';
  budget_amount: number | null;
  budget_currency: string;
  start_date: string | null;
  end_date: string | null;
  channels: string[];
  objective: string | null;
  created_by: string;
  ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

export type CreateCampaignInput = {
  organization_id: string;
  name: string;
  description?: string;
  budget_amount?: number;
  budget_currency?: string;
  start_date?: string;
  end_date?: string;
  channels?: string[];
  objective?: string;
};

export interface CampaignBudget {
  id: string;
  campaign_id: string;
  total_budget: number;
  spent: number;
  remaining: number;
  spend_pct: number;
  currency: string;
  alert_threshold: number;
  is_alert_triggered: boolean;
  period_start: string | null;
  period_end: string | null;
}

export interface CampaignTemplateSummary {
  id: string;
  name: string;
  description: string;
  channels: string[];
  objective: string | null;
  budget_amount: number | null;
  budget_currency: string;
  default_duration_days: number;
  created_by: string;
}

export interface CampaignTemplate extends CampaignTemplateSummary {
  config: Record<string, unknown>;
}

export interface ABTestSummary {
  id: string;
  name: string;
  status: string;
  goal_metric: string;
  winner_variant_id: string | null;
  variants_count: number;
  created_at: string;
}

export interface ABTestVariant {
  id: string;
  name: string;
  description: string;
  traffic_percent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  ctr: number;
  conversion_rate: number;
  cpa: number;
}

export interface ABTest extends ABTestSummary {
  campaign_id: string;
  description: string;
  start_date: string | null;
  end_date: string | null;
  variants: ABTestVariant[];
}
