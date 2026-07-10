import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CampaignBudget, CampaignTemplate, ABTest } from '../types';

const KEYS = {
  budgets: 'campaign-budgets',
  templates: 'campaign-templates',
  abtests: 'ab-tests',
};

// ── Budget ──────────────────────────────────────────────────────────────────

export function useCampaignBudget(campaignId: string) {
  return useQuery<CampaignBudget>({
    queryKey: [KEYS.budgets, campaignId],
    queryFn: () => api.get<CampaignBudget>(`/campaigns/${campaignId}/budget`),
    enabled: !!campaignId,
    retry: false,
  });
}

export function useSetCampaignBudget(campaignId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { total_budget: number; currency?: string; alert_threshold?: number }) =>
      api.put(`/campaigns/${campaignId}/budget`, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.budgets, campaignId] }),
  });
}

export function useRecordSpend(campaignId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (amount: number) =>
      api.post(`/campaigns/${campaignId}/budget/spend`, { amount }),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.budgets, campaignId] }),
  });
}

// ── Templates ────────────────────────────────────────────────────────────────

export function useTemplates(orgId: string) {
  return useQuery<CampaignTemplate[]>({
    queryKey: [KEYS.templates, orgId],
    queryFn: () => api.get<CampaignTemplate[]>(`/campaigns/templates?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useTemplate(id: string) {
  return useQuery<CampaignTemplate>({
    queryKey: [KEYS.templates, id],
    queryFn: () => api.get<CampaignTemplate>(`/campaigns/templates/${id}`),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      name: string;
      description?: string;
      channels?: string[];
      objective?: string | null;
      budget_amount?: number | null;
      budget_currency?: string;
      default_duration_days?: number;
      config?: Record<string, unknown>;
    }) => api.post('/campaigns/templates', input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.templates] }),
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/campaigns/templates/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.templates] }),
  });
}

export function useCloneFromTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { template_id: string; organization_id: string; name: string; start_date?: string }) =>
      api.post('/campaigns/from-template', input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });
}

// ── A/B Tests ────────────────────────────────────────────────────────────────

export function useABTests(campaignId: string) {
  return useQuery<ABTest[]>({
    queryKey: [KEYS.abtests, campaignId],
    queryFn: () => api.get<ABTest[]>(`/campaigns/${campaignId}/ab-tests`),
    enabled: !!campaignId,
  });
}

export function useABTest(id: string) {
  return useQuery<ABTest>({
    queryKey: [KEYS.abtests, id],
    queryFn: () => api.get<ABTest>(`/campaigns/ab-tests/${id}`),
    enabled: !!id,
  });
}

export function useCreateABTest(campaignId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string; description?: string; goal_metric?: string }) =>
      api.post<{ id: string }>(`/campaigns/${campaignId}/ab-tests`, { ...input, campaign_id: campaignId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.abtests, campaignId] }),
  });
}

export function useAddVariant(testId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string; description?: string; traffic_percent: number; config?: Record<string, unknown> }) =>
      api.post(`/campaigns/ab-tests/${testId}/variants`, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.abtests] }),
  });
}

export function useStartABTest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (testId: string) => api.post(`/campaigns/ab-tests/${testId}/start`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.abtests] }),
  });
}

export function useDetermineWinner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (testId: string) => api.post(`/campaigns/ab-tests/${testId}/determine-winner`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.abtests] }),
  });
}

export function useRecordMetrics(testId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { variant_name: string; impressions?: number; clicks?: number; conversions?: number; spend?: number }) =>
      api.post(`/campaigns/ab-tests/${testId}/metrics`, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEYS.abtests] }),
  });
}
