import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Campaign, CreateCampaignInput } from '../types';

const CAMPAIGNS_KEY = 'campaigns';

export function useCampaigns(orgId: string, status?: string) {
  const params = new URLSearchParams({ organization_id: orgId });
  if (status) params.set('status', status);

  return useQuery<Campaign[]>({
    queryKey: [CAMPAIGNS_KEY, orgId, status],
    queryFn: () => api.get<Campaign[]>(`/campaigns?${params}`),
    enabled: !!orgId,
  });
}

export function useCampaign(id: string) {
  return useQuery<Campaign>({
    queryKey: [CAMPAIGNS_KEY, id],
    queryFn: () => api.get<Campaign>(`/campaigns/${id}`),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateCampaignInput) =>
      api.post<Campaign>('/campaigns', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGNS_KEY] });
    },
  });
}

export function useUpdateCampaign(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Partial<CreateCampaignInput & { status: string }>) =>
      api.patch<Campaign>(`/campaigns/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGNS_KEY] });
    },
  });
}
