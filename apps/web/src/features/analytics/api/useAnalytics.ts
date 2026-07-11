import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Overview {
  total_campaigns: number;
  active_campaigns: number;
  draft_campaigns: number;
  completed_campaigns: number;
  total_content: number;
  published_content: number;
  total_budget: number;
  status_breakdown: Record<string, number>;
}

export interface CampaignPerformance {
  id: string;
  name: string;
  status: string;
  budget: number;
  channels: string[];
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  roi: number;
}

export interface AdPerformance {
  total_impressions: number;
  total_clicks: number;
  total_spend: number;
  total_conversions: number;
  total_revenue: number;
  total_budget: number;
  ctr: number;
  cpc: number;
  conversion_rate: number;
  roi: number;
  platforms: {
    name: string;
    campaigns: {
      id: string;
      name: string;
      spend: number;
      impressions: number;
      clicks: number;
      conversions: number;
      revenue: number;
    }[];
  }[];
}

export function useAnalyticsOverview(orgId: string) {
  return useQuery<Overview>({
    queryKey: ['analytics', 'overview', orgId],
    queryFn: () => api.get<Overview>(`/analytics/overview?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useCampaignPerformance(orgId: string) {
  return useQuery<CampaignPerformance[]>({
    queryKey: ['analytics', 'campaigns', orgId],
    queryFn: () => api.get<CampaignPerformance[]>(`/analytics/campaigns?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useAdPerformance() {
  return useQuery<AdPerformance>({
    queryKey: ['analytics', 'ads'],
    queryFn: () => api.get<AdPerformance>('/analytics/ads'),
  });
}
