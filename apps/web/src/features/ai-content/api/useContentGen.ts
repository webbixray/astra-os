import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface BrandVoice {
  id: string;
  name: string;
  tone: string;
  style_guide: string;
  target_audience: string;
  is_active: boolean;
  vocabulary: string[];
  created_at: string;
}

export interface ContentTemplate {
  id: string;
  name: string;
  content_type: string;
  description: string;
  sections: { name: string; prompt: string }[];
  variables: string[];
  is_builtin: boolean;
  created_at: string;
}

export interface GenerateResult {
  content: string;
  sections: Record<string, string>;
  template_name: string;
  content_type: string;
}

export interface SEOScore {
  score: number;
  max_score: number;
  rating: string;
  details: Record<string, unknown>;
}

export function useBrandVoices(orgId: string) {
  return useQuery<BrandVoice[]>({
    queryKey: ['brand-voices', orgId],
    queryFn: () => api.get<BrandVoice[]>(`/brand-voices?organization_id=${orgId}`),
  });
}

export function useCreateBrandVoice() {
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      name: string;
      tone?: string;
      vocabulary?: string[];
      style_guide?: string;
      target_audience?: string;
    }) => api.post<BrandVoice>('/brand-voices', input),
  });
}

export function useContentTemplates(orgId: string) {
  return useQuery<ContentTemplate[]>({
    queryKey: ['content-templates', orgId],
    queryFn: () =>
      api.get<ContentTemplate[]>(
        `/content/templates?organization_id=${orgId}&include_builtin=true`,
      ),
  });
}

export function useContentTemplate(id: string) {
  return useQuery<ContentTemplate>({
    queryKey: ['content-template', id],
    queryFn: () => api.get<ContentTemplate>(`/content/templates/${id}`),
    enabled: !!id,
  });
}

export function useGenerateContent() {
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      template_id: string;
      variables?: Record<string, string>;
      brand_voice_id?: string;
      tone?: string;
      instructions?: string;
    }) => api.post<GenerateResult>('/ai/content/generate', input),
  });
}

export function useRewriteContent() {
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      content: string;
      tone?: string;
      brand_voice_id?: string;
      instructions?: string;
    }) => api.post<{ content: string }>('/ai/content/rewrite', input),
  });
}

export function useBulkGenerate() {
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      template_id: string;
      variable_rows: Record<string, string>[];
      brand_voice_id?: string;
      tone?: string;
    }) => api.post<{ results: GenerateResult[]; total: number }>(
      '/ai/content/generate/bulk',
      input,
    ),
  });
}

export function useSEOScore() {
  return useMutation({
    mutationFn: (input: { content: string; target_keywords?: string[] }) =>
      api.post<SEOScore>('/ai/content/seo-score', input),
  });
}
