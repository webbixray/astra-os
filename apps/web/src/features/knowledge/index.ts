/** Knowledge Intelligence feature — RAG, optimization, cross-campaign learning. */

// Components
export { RAGSearch } from './components/rag-search';
export { OptimizationDashboard } from './components/optimization-dashboard';
export { KnowledgeGraph } from './components/knowledge-graph';

// API hooks
export {
  useRAGSearch,
  useRAGContext,
  useIngestBrandGuidelines,
  useBudgetOptimization,
  useCreativeFatigue,
  useAudienceExpansion,
  useOptimizationSuggestions,
  useMinePatterns,
  useTransferSuggestions,
  useLearningInsights,
} from './api/useKnowledge';

// Types
export type {
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
} from './types';

export {
  RELEVANCE_COLORS,
  URGENCY_COLORS,
  PATTERN_TYPE_LABELS,
  PRIORITY_COLORS,
} from './types';
