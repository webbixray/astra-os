'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { AutonomyConfig, AgentAction, ActionExplanation, AuditSummary } from '../types';

/** Get autonomy config for an organization. */
export function useAutonomyConfig(
  organizationId: string,
  enabled: boolean = true,
) {
  return useQuery<AutonomyConfig>({
    queryKey: ['autonomy-config', organizationId],
    queryFn: async () => {
      const { data } = await apiClient.get(
        '/api/v1/governance/autonomy/config',
        { params: { organization_id: organizationId } },
      );
      return data;
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
      const { data } = await apiClient.put('/api/v1/governance/autonomy/config', {
        organization_id: organizationId,
        default_level: defaultLevel,
        agent_levels: agentLevels,
        auto_approve_spend_limit: autoApproveSpendLimit,
      });
      return data;
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
      const params: Record<string, string | number> = {
        organization_id: organizationId,
      };
      if (options?.agentType) params.agent_type = options.agentType;
      if (options?.actionName) params.action_name = options.actionName;
      if (options?.limit) params.limit = options.limit;
      if (options?.offset) params.offset = options.offset;
      const { data } = await apiClient.get(
        '/api/v1/governance/autonomy/actions',
        { params },
      );
      return data;
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
      const { data } = await apiClient.get(
        `/api/v1/governance/autonomy/explain/${actionId}`,
      );
      return data;
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
      const { data } = await apiClient.get(
        '/api/v1/governance/autonomy/summary',
        { params: { organization_id: organizationId } },
      );
      return data;
    },
    enabled: enabled && !!organizationId,
  });
}
