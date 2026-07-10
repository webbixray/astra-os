import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ContentPublishEntry } from '../types';

const KEYS = {
  queue: 'content-publishing-queue',
  history: 'content-publishing-history',
};

export function usePublishingQueue(orgId: string, status?: string) {
  const params = new URLSearchParams({ organization_id: orgId });
  if (status) params.set('status', status);

  return useQuery<ContentPublishEntry[]>({
    queryKey: [KEYS.queue, orgId, status],
    queryFn: () => api.get<ContentPublishEntry[]>(`/content/publishing/queue?${params}`),
    refetchInterval: 15_000,
  });
}

export function usePublishingHistory(contentId: string) {
  return useQuery<ContentPublishEntry[]>({
    queryKey: [KEYS.history, contentId],
    queryFn: () => api.get<ContentPublishEntry[]>(`/content/${contentId}/publishing-history`),
    enabled: !!contentId,
  });
}

export function usePublishContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { content_id: string; platform: string; scheduled_at?: string; metadata?: Record<string, unknown> }) =>
      api.post<{ id: string; status: string; external_url?: string; error_message?: string }>(
        `/content/${input.content_id}/publish`,
        { platform: input.platform, scheduled_at: input.scheduled_at, metadata: input.metadata },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEYS.queue] });
      qc.invalidateQueries({ queryKey: [KEYS.history] });
    },
  });
}

export function useScheduleContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { content_id: string; platform: string; scheduled_at: string; metadata?: Record<string, unknown> }) =>
      api.post(`/content/${input.content_id}/schedule`, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEYS.queue] });
    },
  });
}

export function useRetryPublish() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (publishId: string) =>
      api.post(`/content/publishing/${publishId}/retry`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEYS.queue] });
      qc.invalidateQueries({ queryKey: [KEYS.history] });
    },
  });
}

export function useCancelPublish() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (publishId: string) =>
      api.delete(`/content/publishing/${publishId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEYS.queue] });
      qc.invalidateQueries({ queryKey: [KEYS.history] });
    },
  });
}
