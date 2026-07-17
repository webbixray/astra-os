'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface PacingData {
  campaign_id: string;
  strategy: string;
  status: string;
  daily_target: number;
  total_budget: number;
  total_spent: number;
  remaining_budget: number;
  days_elapsed: number;
  days_remaining: number;
  percent_time_elapsed: number;
  percent_budget_spent: number;
  pace_ratio: number;
  recommended_daily_limit: number;
  should_pause: boolean;
  alert_message: string | null;
}

interface PacingSchedule {
  campaign_id: string;
  strategy: string;
  total_budget: number;
  schedule: Array<{
    day: string;
    target: number;
    cumulative_target: number;
  }>;
}

export function useCampaignPacing(
  campaignId: string,
  strategy: string = 'even',
  enabled: boolean = true,
) {
  return useQuery<PacingData>({
    queryKey: ['campaign-pacing', campaignId, strategy],
    queryFn: async () => {
      return api.get<PacingData>(
        `/api/v1/campaigns/${campaignId}/pacing?strategy=${strategy}`,
      );
    },
    enabled: enabled && !!campaignId,
    refetchInterval: 60_000, // Refresh every minute
  });
}

export function usePacingSchedule(
  campaignId: string,
  strategy: string = 'even',
  enabled: boolean = true,
) {
  return useQuery<PacingSchedule>({
    queryKey: ['pacing-schedule', campaignId, strategy],
    queryFn: async () => {
      return api.get<PacingSchedule>(
        `/api/v1/campaigns/${campaignId}/pacing/schedule?strategy=${strategy}`,
      );
    },
    enabled: enabled && !!campaignId,
  });
}
