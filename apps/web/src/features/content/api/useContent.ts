import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Content, CreateContentInput } from '../types';

const CONTENT_KEY = 'content';

export function useContentList(orgId: string, status?: string) {
  const params = new URLSearchParams({ organization_id: orgId });
  if (status) params.set('status', status);

  return useQuery<Content[]>({
    queryKey: [CONTENT_KEY, orgId, status],
    queryFn: () => api.get<Content[]>(`/content?${params}`),
  });
}

export function useContent(id: string) {
  return useQuery<Content>({
    queryKey: [CONTENT_KEY, id],
    queryFn: () => api.get<Content>(`/content/${id}`),
    enabled: !!id,
  });
}

export function useCreateContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateContentInput) =>
      api.post<Content>('/content', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTENT_KEY] });
    },
  });
}

export function useUpdateContent(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Partial<CreateContentInput & { status: string }>) =>
      api.patch<Content>(`/content/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTENT_KEY] });
    },
  });
}
