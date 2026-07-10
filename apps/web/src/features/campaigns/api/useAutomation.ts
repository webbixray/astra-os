import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface BudgetRule {
  id: string;
  campaign_id: string;
  name: string;
  strategy: string;
  allocations: Record<string, number>;
  enabled: boolean;
}

export interface BidRule {
  id: string;
  ad_account_id: string;
  name: string;
  strategy: string;
  target_value: number;
  min_bid: number;
  max_bid: number;
  enabled: boolean;
}

export interface AudienceSegment {
  id: string;
  name: string;
  source: string;
  predicted_size: number;
  confidence_score: number;
  criteria: Record<string, unknown>;
}

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence_score: number;
  applied: boolean;
}

export interface AutomationRule {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  action_type: string;
  enabled: boolean;
  execution_count: number;
  last_triggered_at: string | null;
}

// Budget Allocation
export function useBudgetRules(orgId: string) {
  return useQuery<BudgetRule[]>({
    queryKey: ['automation', 'budget-rules', orgId],
    queryFn: () => api.get<BudgetRule[]>(`/automation/budget-rules?organization_id=${orgId}`),
  });
}

export function useCreateBudgetRule(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { campaign_id: string; name: string; strategy?: string; allocations?: Record<string, number> }) =>
      api.post(`/automation/budget-rules?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'budget-rules'] }),
  });
}

export function useCalculateAllocation() {
  return useMutation({
    mutationFn: (ruleId: string) =>
      api.post<Record<string, number>>(`/automation/budget-rules/${ruleId}/calculate`, {}),
  });
}

// Bid Optimization
export function useBidRules(orgId: string) {
  return useQuery<BidRule[]>({
    queryKey: ['automation', 'bid-rules', orgId],
    queryFn: () => api.get<BidRule[]>(`/automation/bid-rules?organization_id=${orgId}`),
  });
}

export function useCreateBidRule(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { ad_account_id: string; name: string; strategy?: string; target_value?: number; min_bid?: number; max_bid?: number }) =>
      api.post(`/automation/bid-rules?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'bid-rules'] }),
  });
}

// Audience Segments
export function useAudienceSegments(orgId: string) {
  return useQuery<AudienceSegment[]>({
    queryKey: ['automation', 'audience-segments', orgId],
    queryFn: () => api.get<AudienceSegment[]>(`/automation/audience-segments?organization_id=${orgId}`),
  });
}

export function useCreateAudienceSegment(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; source?: string; criteria?: Record<string, unknown> }) =>
      api.post(`/automation/audience-segments?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'audience-segments'] }),
  });
}

// Recommendations
export function useRecommendations(orgId: string) {
  return useQuery<Recommendation[]>({
    queryKey: ['automation', 'recommendations', orgId],
    queryFn: () => api.get<Recommendation[]>(`/automation/recommendations?organization_id=${orgId}`),
  });
}

export function useGenerateRecommendations(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (campaignId?: string) =>
      api.post(`/automation/recommendations/generate?organization_id=${orgId}${campaignId ? `&campaign_id=${campaignId}` : ''}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'recommendations'] }),
  });
}

export function useApplyRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (recId: string) => api.post(`/automation/recommendations/${recId}/apply`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'recommendations'] }),
  });
}

// Automation Rules
export function useAutomationRules(orgId: string) {
  return useQuery<AutomationRule[]>({
    queryKey: ['automation', 'rules', orgId],
    queryFn: () => api.get<AutomationRule[]>(`/automation/rules?organization_id=${orgId}`),
  });
}

export function useCreateAutomationRule(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; trigger_type: string; action_type: string; trigger_config?: Record<string, unknown>; action_config?: Record<string, unknown>; description?: string }) =>
      api.post(`/automation/rules?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'rules'] }),
  });
}

export function useToggleAutomationRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) =>
      api.patch(`/automation/rules/${ruleId}/toggle?enabled=${enabled}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'rules'] }),
  });
}

export function useEvaluateRules(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/automation/rules/evaluate?organization_id=${orgId}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'rules'] }),
  });
}

export function useDeleteAutomationRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: string) => api.delete(`/automation/rules/${ruleId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation', 'rules'] }),
  });
}
