'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { ApprovalRule, ApprovalRequest } from '../types';

/** List pending approval requests for an organization. */
export function usePendingApprovals(
  organizationId: string,
  role?: string,
  enabled: boolean = true,
) {
  return useQuery<{ items: ApprovalRequest[]; total: number }>({
    queryKey: ['pending-approvals', organizationId, role],
    queryFn: async () => {
      const params: Record<string, string> = { organization_id: organizationId };
      if (role) params.role = role;
      const { data } = await apiClient.get(
        '/api/v1/governance/approval/requests/pending',
        { params },
      );
      return data;
    },
    enabled: enabled && !!organizationId,
    refetchInterval: 30_000, // Refresh every 30s for real-time queue
  });
}

/** List approval rules for an organization. */
export function useApprovalRules(
  organizationId: string,
  enabled: boolean = true,
) {
  return useQuery<{ items: ApprovalRule[]; total: number }>({
    queryKey: ['approval-rules', organizationId],
    queryFn: async () => {
      const { data } = await apiClient.get(
        '/api/v1/governance/approval/rules',
        { params: { organization_id: organizationId } },
      );
      return data;
    },
    enabled: enabled && !!organizationId,
  });
}

/** Approve or reject an approval request. */
export function useDecideApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      requestId,
      action,
      reason,
    }: {
      requestId: string;
      action: 'approve' | 'reject';
      reason?: string;
    }) => {
      const { data } = await apiClient.post(
        `/api/v1/governance/approval/requests/${requestId}/decide`,
        { action, reason: reason || '' },
      );
      return data;
    },
    onSuccess: () => {
      // Invalidate pending approvals to refresh the queue
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
    },
  });
}

/** Evaluate approval rules against a context. */
export function useEvaluateRules(organizationId: string) {
  return useMutation({
    mutationFn: async (context: Record<string, unknown>) => {
      const { data } = await apiClient.post(
        '/api/v1/governance/approval/evaluate',
        { organization_id: organizationId, context },
      );
      return data;
    },
  });
}
