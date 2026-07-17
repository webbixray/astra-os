'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AutonomyConfig, AgentAction, ActionExplanation, AuditSummary } from '../types';

/** Get autonomy config for an organization. */
export function useAutonomyConfig(
  organizationId: string,
  enabled: boolean = true,
) {
  return useQuery<AutonomyConfig>({
    queryKey: ['autonomy-config', organizationId],
    queryFn: async () => {
      return api.get<AutonomyConfig>(
        `/api/v1/governance/autonomy/config?organization_id=${organizationId}`,
      );
    },
    enabled: enabled && !!organizationId,
  });
}

/** Update autonomy config. */
export function useUpdateAutonomyConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      organizationId,
      defaultLevel,
      agentLevels,
      autoApproveSpendLimit,
    }: {
      organizationId: string;
      defaultLevel?: number;
      agentLevels?: Record<string, number>;
      autoApproveSpendLimit?: number;
    }) => {
      return api.put<unknown>('/api/v1/governance/autonomy/config', {
        organization_id: organizationId,
        default_level: defaultLevel,
        agent_levels: agentLevels,
        auto_approve_spend_limit: autoApproveSpendLimit,
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['autonomy-config', variables.organizationId],
      });
    },
  });
}

/** List agent actions for an organization. */
export function useAgentActions(
  organizationId: string,
  options?: {
    agentType?: string;
    actionName?: string;
    limit?: number;
    offset?: number;
  },
  enabled: boolean = true,
) {
  return useQuery<{ items: AgentAction[]; total: number }>({
    queryKey: ['agent-actions', organizationId, options],
    queryFn: async () => {
      const params = new URLSearchParams({ organization_id: organizationId });
      if (options?.agentType) params.set('agent_type', options.agentType);
      if (options?.actionName) params.set('action_name', options.actionName);
      if (options?.limit) params.set('limit', String(options.limit));
      if (options?.offset) params.set('offset', String(options.offset));
      return api.get<{ items: AgentAction[]; total: number }>(
        `/api/v1/governance/autonomy/actions?${params.toString()}`,
      );
    },
    enabled: enabled && !!organizationId,
  });
}

/** Get explanation for a specific agent action. */
export function useActionExplanation(
  actionId: string,
  enabled: boolean = true,
) {
  return useQuery<ActionExplanation>({
    queryKey: ['action-explanation', actionId],
    queryFn: async () => {
      return api.get<ActionExplanation>(
        `/api/v1/governance/autonomy/explain/${actionId}`,
      );
    },
    enabled: enabled && !!actionId,
  });
}

/** Get audit summary for an organization. */
export function useAuditSummary(
  organizationId: string,
  enabled: boolean = true,
) {
  return useQuery<AuditSummary>({
    queryKey: ['audit-summary', organizationId],
    queryFn: async () => {
      return api.get<AuditSummary>(
        `/api/v1/governance/autonomy/summary?organization_id=${organizationId}`,
      );
    },
    enabled: enabled && !!organizationId,
  });
}
