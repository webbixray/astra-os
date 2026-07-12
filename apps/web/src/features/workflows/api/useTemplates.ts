import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  WorkflowTemplateSummary,
  WorkflowTemplateDetail,
  InstantiateTemplateInput,
  InstantiatedWorkflow,
} from '../types';

const TEMPLATES_KEY = 'workflow-templates';

export function useWorkflowTemplates(category?: string) {
  const params = category ? `?category=${category}` : '';

  return useQuery<WorkflowTemplateSummary[]>({
    queryKey: [TEMPLATES_KEY, category],
    queryFn: () => api.get<WorkflowTemplateSummary[]>(`/workflows/templates${params}`),
  });
}

export function useWorkflowTemplate(templateId: string) {
  return useQuery<WorkflowTemplateDetail>({
    queryKey: [TEMPLATES_KEY, templateId],
    queryFn: () => api.get<WorkflowTemplateDetail>(`/workflows/templates/${templateId}`),
    enabled: !!templateId,
  });
}

export function useInstantiateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      input,
    }: {
      templateId: string;
      input: InstantiateTemplateInput;
    }) =>
      api.post<InstantiatedWorkflow>(
        `/workflows/templates/${templateId}/instantiate`,
        input,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}
