import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface CalendarEvent {
  id: string;
  type: 'campaign' | 'content' | 'ad_campaign';
  title: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  link: string | null;
}

export interface CampaignOverview {
  total_campaigns: number;
  total_ad_campaigns: number;
  campaign_status_breakdown: Record<string, number>;
  ad_campaign_status_breakdown: Record<string, number>;
  ad_platform_breakdown: Record<string, number>;
  combined_total: number;
}

export function useCalendarEvents(
  orgId: string,
  startDate: string,
  endDate: string,
) {
  return useQuery<CalendarEvent[]>({
    queryKey: ['calendar', 'events', orgId, startDate, endDate],
    queryFn: () =>
      api.get<CalendarEvent[]>(
        `/calendar/events?organization_id=${orgId}&start_date=${startDate}&end_date=${endDate}`,
      ),
  });
}

export function useCampaignOverview(orgId: string) {
  return useQuery<CampaignOverview>({
    queryKey: ['campaigns', 'overview', orgId],
    queryFn: () =>
      api.get<CampaignOverview>(`/campaigns/overview?organization_id=${orgId}`),
  });
}
