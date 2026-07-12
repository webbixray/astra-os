'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type {
  SearchResult,
  RAGContextResponse,
  IngestionResponse,
  BudgetAllocation,
  CreativeFatigueResult,
  AudienceExpansionSuggestion,
  OptimizationSuggestion,
  CampaignPattern,
  TransferRecommendation,
  LearningInsight,
} from '../types';

// ---------------------------------------------------------------------------
// RAG hooks
// ---------------------------------------------------------------------------

/** Hybrid search across the knowledge graph. */
export function useRAGSearch(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      query,
      typeFilter,
      limit,
      minScore,
    }: {
      query: string;
      typeFilter?: string;
      limit?: number;
      minScore?: number;
    }) => {
      const { data } = await apiClient.post<{ results: SearchResult[]; total: number }>(
        '/api/v1/knowledge/rag/search',
        {
          organization_id: organizationId,
          query,
          type_filter: typeFilter || null,
          limit: limit || 10,
          min_score: minScore || 0.3,
        },
      );
      return data;
    },
  });
}

/** Assemble context for an agent prompt. */
export function useRAGContext(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      query,
      userId,
      agentId,
      maxResults,
      includeBrandGuidelines,
      includeMemories,
    }: {
      query: string;
      userId?: string;
      agentId?: string;
      maxResults?: number;
      includeBrandGuidelines?: boolean;
      includeMemories?: boolean;
    }) => {
      const { data } = await apiClient.post<RAGContextResponse>(
        '/api/v1/knowledge/rag/context',
        {
          organization_id: organizationId,
          query,
          user_id: userId || null,
          agent_id: agentId || null,
          max_results: maxResults || 10,
          include_brand_guidelines: includeBrandGuidelines ?? true,
          include_memories: includeMemories ?? true,
        },
      );
      return data;
    },
  });
}

/** Ingest brand guidelines into the knowledge graph. */
export function useIngestBrandGuidelines() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      organizationId,
      guidelinesText,
      name,
    }: {
      organizationId: string;
      guidelinesText: string;
      name?: string;
    }) => {
      const { data } = await apiClient.post<IngestionResponse>(
        '/api/v1/knowledge/rag/ingest/brand-guidelines',
        {
          organization_id: organizationId,
          guidelines_text: guidelinesText,
          name: name || 'Brand Guidelines',
        },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Optimization hooks
// ---------------------------------------------------------------------------

/** Optimize budget allocation across campaigns. */
export function useBudgetOptimization(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      campaigns,
      totalBudget,
    }: {
      campaigns: Array<{
        id: string;
        name: string;
        daily_budget: number;
        roas: number;
        impressions: number;
        clicks: number;
        conversions: number;
        spend: number;
      }>;
      totalBudget?: number;
    }) => {
      const { data } = await apiClient.post<{
        allocations: BudgetAllocation[];
        total_campaigns: number;
      }>('/api/v1/knowledge/optimization/budget', {
        organization_id: organizationId,
        campaigns,
        total_budget: totalBudget || null,
      });
      return data;
    },
  });
}

/** Detect creative fatigue from performance data. */
export function useCreativeFatigue(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      creatives,
    }: {
      creatives: Array<{
        id: string;
        name: string;
        ctr_history: number[];
        current_ctr: number;
        peak_ctr: number;
      }>;
    }) => {
      const { data } = await apiClient.post<{
        results: CreativeFatigueResult[];
        total_creatives: number;
        fatigued_count: number;
      }>('/api/v1/knowledge/optimization/creative-fatigue', {
        organization_id: organizationId,
        creatives,
      });
      return data;
    },
  });
}

/** Suggest audience expansion targets. */
export function useAudienceExpansion(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      sourceAudience,
      limit,
    }: {
      sourceAudience: string;
      limit?: number;
    }) => {
      const { data } = await apiClient.post<{
        suggestions: AudienceExpansionSuggestion[];
        source_audience: string;
        total_suggestions: number;
      }>('/api/v1/knowledge/optimization/audience-expansion', {
        organization_id: organizationId,
        source_audience: sourceAudience,
        limit: limit || 5,
      });
      return data;
    },
  });
}

/** Generate unified optimization suggestions. */
export function useOptimizationSuggestions(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      campaigns,
    }: {
      campaigns: Array<{
        id: string;
        name: string;
        daily_budget: number;
        roas: number;
        impressions: number;
        clicks: number;
        conversions: number;
        spend: number;
      }>;
    }) => {
      const { data } = await apiClient.post<{
        suggestions: OptimizationSuggestion[];
        total: number;
      }>('/api/v1/knowledge/optimization/suggestions', {
        organization_id: organizationId,
        campaigns,
      });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Cross-campaign learning hooks
// ---------------------------------------------------------------------------

/** Mine patterns across campaigns. */
export function useMinePatterns(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      campaignIds,
      patternTypes,
      limit,
    }: {
      campaignIds?: string[];
      patternTypes?: string[];
      limit?: number;
    }) => {
      const { data } = await apiClient.post<{
        patterns: CampaignPattern[];
        total: number;
      }>('/api/v1/knowledge/patterns/mine', {
        organization_id: organizationId,
        campaign_ids: campaignIds || null,
        pattern_types: patternTypes || null,
        limit: limit || 10,
      });
      return data;
    },
  });
}

/** Suggest pattern transfers to a target campaign. */
export function useTransferSuggestions(organizationId: string) {
  return useMutation({
    mutationFn: async ({
      targetCampaignId,
      limit,
    }: {
      targetCampaignId: string;
      limit?: number;
    }) => {
      const { data } = await apiClient.post<{
        recommendations: TransferRecommendation[];
        target_campaign_id: string;
        total: number;
      }>('/api/v1/knowledge/patterns/transfer', {
        organization_id: organizationId,
        target_campaign_id: targetCampaignId,
        limit: limit || 5,
      });
      return data;
    },
  });
}

/** Get aggregated learning insights. */
export function useLearningInsights(organizationId: string, enabled: boolean = true) {
  return useQuery<{ insights: LearningInsight[]; total: number }>({
    queryKey: ['learning-insights', organizationId],
    queryFn: async () => {
      const { data } = await apiClient.post<{
        insights: LearningInsight[];
        total: number;
      }>('/api/v1/knowledge/patterns/insights', {
        organization_id: organizationId,
        limit: 10,
      });
      return data;
    },
    enabled: enabled && !!organizationId,
  });
}
