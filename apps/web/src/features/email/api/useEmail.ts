import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EmailProvider, EmailCampaign, EmailAnalytics } from '../types';

const KEYS = {
  providers: 'email-providers',
  campaigns: 'email-campaigns',
  analytics: 'email-analytics',
};

// ── Providers ──────────────────────────────────────────────────────────────

export function useEmailProviders(orgId: string) {
  return useQuery<EmailProvider[]>({
    queryKey: [KEYS.providers, orgId],
    queryFn: () => api.get<EmailProvider[]>(`/email/providers?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useCreateEmailProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      provider_type: string;
      name: string;
      api_key: string;
      from_email: string;
      from_name?: string;
    }) => api.post('/email/providers', input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.providers] }),
  });
}

export function useDeleteEmailProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/email/providers/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.providers] }),
  });
}

// ── Campaigns ──────────────────────────────────────────────────────────────

export function useEmailCampaigns(orgId: string, status?: string) {
  const params = new URLSearchParams({ organization_id: orgId });
  if (status) params.set('status', status);

  return useQuery<EmailCampaign[]>({
    queryKey: [KEYS.campaigns, orgId, status],
    queryFn: () => api.get<EmailCampaign[]>(`/email/campaigns?${params}`),
  });
}

export function useEmailCampaign(id: string) {
  return useQuery<EmailCampaign>({
    queryKey: [KEYS.campaigns, id],
    queryFn: () => api.get<EmailCampaign>(`/email/campaigns/${id}`),
    enabled: !!id,
  });
}

export function useCreateEmailCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      provider_id: string;
      name: string;
      subject: string;
      body: string;
      from_email: string;
      from_name?: string;
      scheduled_at?: string;
    }) => api.post('/email/campaigns', input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.campaigns] }),
  });
}

export function useSendEmailCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { campaign_id: string; recipients: string[] }) =>
      api.post(`/email/campaigns/${input.campaign_id}/send`, { recipients: input.recipients }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEYS.campaigns] });
    },
  });
}

export function useDeleteEmailCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/email/campaigns/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.campaigns] }),
  });
}

// ── Analytics ──────────────────────────────────────────────────────────────

export function useEmailAnalytics(orgId: string) {
  return useQuery<EmailAnalytics>({
    queryKey: [KEYS.analytics, orgId],
    queryFn: () => api.get<EmailAnalytics>(`/email/analytics?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}
