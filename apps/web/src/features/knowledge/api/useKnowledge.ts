'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
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
      return api.post<{ results: SearchResult[]; total: number }>(
        '/api/v1/knowledge/rag/search',
        {
          organization_id: organizationId,
          query,
          type_filter: typeFilter || null,
          limit: limit || 10,
          min_score: minScore || 0.3,
        },
      );
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
      return api.post<RAGContextResponse>(
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
      return api.post<IngestionResponse>(
        '/api/v1/knowledge/rag/ingest/brand-guidelines',
        {
          organization_id: organizationId,
          guidelines_text: guidelinesText,
          name: name || 'Brand Guidelines',
        },
      );
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
      return api.post<{
        allocations: BudgetAllocation[];
        total_campaigns: number;
      }>('/api/v1/knowledge/optimization/budget', {
        organization_id: organizationId,
        campaigns,
        total_budget: totalBudget || null,
      });
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
      return api.post<{
        results: CreativeFatigueResult[];
        total_creatives: number;
        fatigued_count: number;
      }>('/api/v1/knowledge/optimization/creative-fatigue', {
        organization_id: organizationId,
        creatives,
      });
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
      return api.post<{
        suggestions: AudienceExpansionSuggestion[];
        source_audience: string;
        total_suggestions: number;
      }>('/api/v1/knowledge/optimization/audience-expansion', {
        organization_id: organizationId,
        source_audience: sourceAudience,
        limit: limit || 5,
      });
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
      return api.post<{
        suggestions: OptimizationSuggestion[];
        total: number;
      }>('/api/v1/knowledge/optimization/suggestions', {
        organization_id: organizationId,
        campaigns,
      });
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
      return api.post<{
        patterns: CampaignPattern[];
        total: number;
      }>('/api/v1/knowledge/patterns/mine', {
        organization_id: organizationId,
        campaign_ids: campaignIds || null,
        pattern_types: patternTypes || null,
        limit: limit || 10,
      });
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
      return api.post<{
        recommendations: TransferRecommendation[];
        target_campaign_id: string;
        total: number;
      }>('/api/v1/knowledge/patterns/transfer', {
        organization_id: organizationId,
        target_campaign_id: targetCampaignId,
        limit: limit || 5,
      });
    },
  });
}

/** Get aggregated learning insights. */
export function useLearningInsights(organizationId: string, enabled: boolean = true) {
  return useQuery<{ insights: LearningInsight[]; total: number }>({
    queryKey: ['learning-insights', organizationId],
    queryFn: async () => {
      return api.post<{
        insights: LearningInsight[];
        total: number;
      }>('/api/v1/knowledge/patterns/insights', {
        organization_id: organizationId,
        limit: 10,
      });
    },
    enabled: enabled && !!organizationId,
  });
}
