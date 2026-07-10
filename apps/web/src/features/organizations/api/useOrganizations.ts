import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface OrgDetail {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OrgTree {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  children: { id: string; name: string; slug: string; plan_tier: string }[];
}

export interface Member {
  id: string;
  user_id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  joined_at: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface FeatureFlag {
  id: string;
  feature_key: string;
  enabled: boolean;
  config: Record<string, unknown>;
}

export interface UsageSummary {
  usage: Record<string, number>;
  limits: Record<string, number | string>;
  plan_tier: string;
  period_start: string;
}

export interface BillingPlan {
  id: string;
  plan_tier: string;
  billing_cycle: string;
  subscription_status: string;
  current_period_start: string;
  current_period_end: string;
  limits: Record<string, number | string>;
}

// ── Org Hierarchy ───────────────────────────────────────────────────────────

export function useOrgTree(orgId: string) {
  return useQuery<OrgTree>({
    queryKey: ['org-tree', orgId],
    queryFn: () => api.get<OrgTree>(`/organizations/${orgId}/tree`),
    enabled: !!orgId,
  });
}

export function useSetParentOrg() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, parentOrgId }: { orgId: string; parentOrgId: string }) =>
      api.post(`/organizations/${orgId}/parent`, { parent_org_id: parentOrgId }),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['org-tree', vars.orgId] });
      qc.invalidateQueries({ queryKey: ['org-tree', vars.parentOrgId] });
    },
  });
}

export function useCreateSubOrg() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, name, slug }: { orgId: string; name: string; slug: string }) =>
      api.post(`/organizations/${orgId}/sub-orgs`, { name, slug }),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['org-tree', vars.orgId] }),
  });
}

// ── Invitations ─────────────────────────────────────────────────────────────

export function useInvitations(orgId: string) {
  return useQuery<Invitation[]>({
    queryKey: ['invitations', orgId],
    queryFn: () => api.get<Invitation[]>(`/organizations/${orgId}/invitations`),
    enabled: !!orgId,
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, email, role }: { orgId: string; email: string; role: string }) =>
      api.post(`/organizations/${orgId}/invitations`, { email, role }),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['invitations', vars.orgId] }),
  });
}

export function useCancelInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, invitationId }: { orgId: string; invitationId: string }) =>
      api.delete(`/organizations/${orgId}/invitations/${invitationId}`),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['invitations', vars.orgId] }),
  });
}

export function useAcceptInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (invitationId: string) =>
      api.post(`/invitations/${invitationId}/accept`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['members'] });
      qc.invalidateQueries({ queryKey: ['invitations'] });
    },
  });
}

// ── Members ─────────────────────────────────────────────────────────────────

export function useMembers(orgId: string) {
  return useQuery<Member[]>({
    queryKey: ['members', orgId],
    queryFn: () => api.get<Member[]>(`/organizations/${orgId}/members`),
    enabled: !!orgId,
  });
}

export function useChangeMemberRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, memberId, role }: { orgId: string; memberId: string; role: string }) =>
      api.patch(`/organizations/${orgId}/members/${memberId}/role`, { role }),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['members', vars.orgId] }),
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, memberId }: { orgId: string; memberId: string }) =>
      api.delete(`/organizations/${orgId}/members/${memberId}`),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['members', vars.orgId] }),
  });
}

// ── Feature Flags ───────────────────────────────────────────────────────────

export function useFeatureFlags(orgId: string) {
  return useQuery<FeatureFlag[]>({
    queryKey: ['feature-flags', orgId],
    queryFn: () => api.get<FeatureFlag[]>(`/organizations/${orgId}/features`),
    enabled: !!orgId,
  });
}

export function useSetFeatureFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, feature_key, enabled, config }: {
      orgId: string; feature_key: string; enabled?: boolean; config?: Record<string, unknown>;
    }) => api.put(`/organizations/${orgId}/features`, { feature_key, enabled, config }),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['feature-flags', vars.orgId] }),
  });
}

// ── Usage & Billing ─────────────────────────────────────────────────────────

export function useUsageSummary(orgId: string) {
  return useQuery<UsageSummary>({
    queryKey: ['usage', orgId],
    queryFn: () => api.get<UsageSummary>(`/organizations/${orgId}/usage`),
    enabled: !!orgId,
  });
}

export function useBillingPlan(orgId: string) {
  return useQuery<BillingPlan>({
    queryKey: ['billing', orgId],
    queryFn: () => api.get<BillingPlan>(`/organizations/${orgId}/billing`),
    enabled: !!orgId,
  });
}

export function useChangeBillingPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, plan_tier }: { orgId: string; plan_tier: string }) =>
      api.put(`/organizations/${orgId}/billing`, { plan_tier }),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['billing', vars.orgId] });
      qc.invalidateQueries({ queryKey: ['org', vars.orgId] });
    },
  });
}

export function useCheckPermission(orgId: string, permission: string) {
  return useQuery<{ has_permission: boolean }>({
    queryKey: ['permission', orgId, permission],
    queryFn: () =>
      api.get<{ has_permission: boolean }>(
        `/organizations/${orgId}/check-permission/${permission}`,
      ),
    enabled: !!orgId && !!permission,
  });
}
