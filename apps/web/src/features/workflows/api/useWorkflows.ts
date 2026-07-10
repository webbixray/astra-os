import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Workflow, CreateWorkflowInput } from '../types';

const WORKFLOWS_KEY = 'workflows';

export function useWorkflows(orgId: string, status?: string) {
  const params = new URLSearchParams({ organization_id: orgId });
  if (status) params.set('status', status);

  return useQuery<Workflow[]>({
    queryKey: [WORKFLOWS_KEY, orgId, status],
    queryFn: () => api.get<Workflow[]>(`/workflows?${params}`),
  });
}

export function useWorkflow(id: string) {
  return useQuery<Workflow>({
    queryKey: [WORKFLOWS_KEY, id],
    queryFn: () => api.get<Workflow>(`/workflows/${id}`),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateWorkflowInput) =>
      api.post<Workflow>('/workflows', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useUpdateWorkflow(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Partial<Workflow>) =>
      api.patch<Workflow>(`/workflows/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useExecuteWorkflow() {
  return useMutation({
    mutationFn: ({
      workflowId,
      orgId,
    }: {
      workflowId: string;
      orgId: string;
    }) =>
      api.post(`/workflows/${workflowId}/execute`, {
        organization_id: orgId,
      }),
  });
}
