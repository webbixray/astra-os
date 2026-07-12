import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { WorkflowExecutionDetail } from '../types';

const EXECUTIONS_KEY = 'workflow-executions';

export function useWorkflowExecutions(workflowId: string) {
  return useQuery<WorkflowExecutionDetail[]>({
    queryKey: [EXECUTIONS_KEY, workflowId],
    queryFn: () =>
      api.get<WorkflowExecutionDetail[]>(`/workflows/${workflowId}/executions`),
    enabled: !!workflowId,
  });
}
