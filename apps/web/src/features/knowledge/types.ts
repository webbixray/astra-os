/** Knowledge Intelligence feature types — RAG, optimization, cross-campaign. */

export interface SearchResult {
  node_id: string;
  node_type: string;
  name: string;
  description: string;
  score: number;
  source: 'vector' | 'keyword' | 'combined' | 'graph';
  relevance: 'high' | 'medium' | 'low';
  properties: Record<string, unknown>;
  related_node_ids: string[];
}

export interface RAGContextResponse {
  query: string;
  context_text: string;
  result_count: number;
  high_relevance_count: number;
  source_node_ids: string[];
  brand_guidelines: string | null;
  memory_context_count: number;
  assembled_at: number;
}

export interface IngestionResponse {
  nodes_created: number;
  relations_created: number;
  memories_created: number;
  errors: string[];
  processing_time_ms: number;
  success: boolean;
}

export interface BudgetAllocation {
  campaign_id: string;
  campaign_name: string;
  current_daily_budget: number;
  suggested_daily_budget: number;
  budget_change_pct: number;
  rationale: string;
  confidence: number;
}

export interface CreativeFatigueResult {
  creative_id: string;
  creative_name: string;
  is_fatigued: boolean;
  decline_rate: number;
  days_since_peak: number;
  current_ctr: number;
  peak_ctr: number;
  recommendation: string;
}

export interface AudienceExpansionSuggestion {
  source_audience: string;
  suggested_audience: string;
  overlap_estimate: number;
  rationale: string;
  confidence: number;
  related_node_ids: string[];
}

export interface OptimizationSuggestion {
  suggestion_type: 'budget_reallocation' | 'creative_fatigue' | 'audience_expansion' | 'budget_increase' | 'budget_decrease';
  title: string;
  description: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  campaign_id: string | null;
  confidence: number;
  estimated_impact: string;
  action_items: string[];
}

export interface CampaignPattern {
  pattern_id: string;
  pattern_type: string;
  title: string;
  description: string;
  campaign_ids: string[];
  strength: number;
  sample_size: number;
  confidence: number;
}

export interface TransferRecommendation {
  source_campaign_id: string;
  source_campaign_name: string;
  target_campaign_id: string;
  target_campaign_name: string;
  pattern: CampaignPattern;
  transfer_strategy: string;
  expected_lift: string;
  confidence: number;
  prerequisites: string[];
}

export interface LearningInsight {
  insight_id: string;
  title: string;
  description: string;
  supporting_campaigns: string[];
  insight_type: string;
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  recommended_actions: string[];
}

/** Color mappings for relevance levels. */
export const RELEVANCE_COLORS: Record<string, string> = {
  high: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-600',
};

/** Color mappings for urgency levels. */
export const URGENCY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-600',
};

/** Color mappings for pattern types. */
export const PATTERN_TYPE_LABELS: Record<string, string> = {
  audience_pattern: 'Audience',
  content_pattern: 'Content',
  timing_pattern: 'Timing',
  channel_pattern: 'Channel',
  budget_pattern: 'Budget',
  creative_pattern: 'Creative',
};

/** Color mappings for insight priority. */
export const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-600',
};
