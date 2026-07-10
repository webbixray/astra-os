export interface AdAccount {
  id: string;
  platform: string;
  account_name: string;
  status: string;
  last_synced_at: string | null;
  created_at: string;
}

export interface AdCampaign {
  id: string;
  ad_account_id: string;
  name: string;
  objective: string;
  status: string;
  platform: string | null;
  sync_status: string;
  daily_budget: number;
  created_at: string;
}

export interface AdCreative {
  id: string;
  name: string;
  type: string;
  status: string;
  headline: string | null;
  created_at: string;
}
