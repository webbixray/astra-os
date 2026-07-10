import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AdAccount, AdCampaign, AdCreative } from '../types';

const AD_KEY = 'advertising';

export function useAdAccounts(orgId: string) {
  return useQuery<AdAccount[]>({
    queryKey: [AD_KEY, 'accounts', orgId],
    queryFn: () => api.get<AdAccount[]>(`/ad/accounts?organization_id=${orgId}`),
  });
}

export function useConnectAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      platform: string;
      account_name: string;
      platform_account_id: string;
      credentials?: Record<string, string>;
    }) => api.post<AdAccount>('/ad/accounts', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'accounts'] });
    },
  });
}

export function useSyncAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: string) =>
      api.post(`/ad/accounts/${accountId}/sync`, {}),
    onSuccess: (_data, _accountId) => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'accounts'] });
    },
  });
}

export function useDisconnectAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: string) =>
      api.post(`/ad/accounts/${accountId}/disconnect`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'accounts'] });
    },
  });
}

export function useAdCampaigns(orgId: string) {
  return useQuery<AdCampaign[]>({
    queryKey: [AD_KEY, 'campaigns', orgId],
    queryFn: () => api.get<AdCampaign[]>(`/ad/campaigns?organization_id=${orgId}`),
  });
}

export function useCreateAdCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      ad_account_id: string;
      name: string;
      objective?: string;
    }) => api.post<AdCampaign>('/ad/campaigns', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'campaigns'] });
    },
  });
}

export function useAdCreatives(orgId: string) {
  return useQuery<AdCreative[]>({
    queryKey: [AD_KEY, 'creatives', orgId],
    queryFn: () => api.get<AdCreative[]>(`/ad/creatives?organization_id=${orgId}`),
  });
}

export function useCreateAdCreative() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      name: string;
      type?: string;
      ad_campaign_id?: string;
    }) => api.post<AdCreative>('/ad/creatives', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'creatives'] });
    },
  });
}

export function useUpdateAdCreative() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      ...input
    }: {
      id: string;
      headline?: string;
      body?: string;
      destination_url?: string;
      status?: string;
    }) => api.patch<AdCreative>(`/ad/creatives/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AD_KEY, 'creatives'] });
    },
  });
}
