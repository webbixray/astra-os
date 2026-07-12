"""RAG Pipeline — Hybrid search + context assembly for agent prompts.

M4 Intelligence: Combines vector similarity search with keyword matching
and knowledge graph traversal to provide rich context for agent decisions.

Builds on existing KnowledgeGraphService + MemoryService + GraphStore.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.application.use_cases.knowledge.knowledge_service import (
    KnowledgeGraphService,
)
from app.application.use_cases.knowledge.memory_service import MemoryService
from app.domain.entities.knowledge.node import NodeType
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """A single search result with relevance metadata."""

    node_id: str
    node_type: str
    name: str
    description: str
    score: float
    source: str  # 'vector', 'keyword', 'graph', 'combined'
    properties: dict[str, Any] = field(default_factory=dict)
    related_node_ids: list[str] = field(default_factory=list)

    @property
    def relevance_label(self) -> str:
        if self.score >= 0.8:
            return "high"
        if self.score >= 0.5:
            return "medium"
        return "low"


@dataclass
class RAGContext:
    """Assembled context for an agent prompt."""

    query: str
    results: list[SearchResult]
    context_text: str
    source_node_ids: list[str]
    brand_guidelines: str | None = None
    memory_context: list[dict[str, Any]] = field(default_factory=list)
    organization_id: str = ""
    agent_id: str | None = None
    assembled_at: float = field(default_factory=time.time)

    @property
    def result_count(self) -> int:
        return len(self.results)

    @property
    def high_relevance_count(self) -> int:
        return sum(1 for r in self.results if r.relevance_label == "high")


@dataclass
class IngestionResult:
    """Result of knowledge ingestion."""

    nodes_created: int = 0
    relations_created: int = 0
    memories_created: int = 0
    errors: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes_created": self.nodes_created,
            "relations_created": self.relations_created,
            "memories_created": self.memories_created,
            "errors": self.errors,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "success": self.success,
        }


# ---------------------------------------------------------------------------
# RAG Pipeline
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "of", "in", "to", "for",
    "with", "on", "at", "from", "by", "about", "as", "into", "through",
    "during", "before", "after", "and", "but", "or", "nor", "not", "so",
    "yet", "both", "this", "that", "these", "those", "it", "its",
})


class RagPipeline:
    """Hybrid search + context assembly for agent prompts.

    Combines vector similarity search with keyword matching
    and knowledge graph traversal to provide rich context.

    Dependencies:
        - KnowledgeGraphService (existing) — CRUD nodes, vector search, relations
        - MemoryService (existing) — remember / recall memories
        - EventBus (existing) — publish domain events
    """

    def __init__(
        self,
        knowledge_service: KnowledgeGraphService,
        memory_service: MemoryService,
    ) -> None:
        self._ks = knowledge_service
        self._ms = memory_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        organization_id: UUID,
        *,
        type_filter: str | None = None,
        limit: int = 10,
        min_score: float = 0.3,
    ) -> list[SearchResult]:
        """Hybrid search combining vector, keyword, and graph traversal."""
        # 1. Vector similarity search (via existing KnowledgeGraphService)
        vector_results = await self._vector_search(
            query, organization_id,
            type_filter=type_filter, limit=limit,
        )

        # 2. Keyword search
        keyword_results = await self._keyword_search(
            query, organization_id,
            type_filter=type_filter, limit=limit,
        )

        # 3. Merge and deduplicate
        merged = self._merge_results(vector_results, keyword_results)

        # 4. Boost results with graph connections
        boosted = await self._boost_with_graph_context(merged)

        # 5. Filter by minimum score and sort
        filtered = [r for r in boosted if r.score >= min_score]
        filtered.sort(key=lambda r: r.score, reverse=True)
        return filtered[:limit]

    async def assemble_context(
        self,
        query: str,
        organization_id: UUID,
        *,
        user_id: UUID | None = None,
        agent_id: str | None = None,
        max_results: int = 10,
        include_brand_guidelines: bool = True,
        include_memories: bool = True,
    ) -> RAGContext:
        """Assemble rich context for an agent prompt."""
        results = await self.search(
            query, organization_id,
            limit=max_results,
        )

        # Build context text
        context_parts: list[str] = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] ({result.node_type}) {result.name}\n"
                f"    {result.description[:500]}\n"
                f"    Source: {result.source} | Relevance: {result.relevance_label}"
            )

        # Add memory context
        memory_ctx: list[dict[str, Any]] = []
        if include_memories and user_id:
            try:
                memories = await self._ms.recall(
                    organization_id=organization_id,
                    user_id=user_id,
                    query=query,
                    limit=3,
                )
                for mem in memories:
                    context_parts.append(
                        f"[Memory] {mem.get('key', '')}: {mem.get('value', '')[:300]}\n"
                        f"    Importance: {mem.get('importance', 'medium')}"
                    )
                    memory_ctx.append(mem)
            except Exception:
                logger.debug("Memory recall failed during context assembly")

        context_text = (
            "\n\n".join(context_parts)
            if context_parts
            else "No relevant context found."
        )

        # Fetch brand guidelines if requested
        brand_guidelines = None
        if include_brand_guidelines:
            brand_guidelines = await self._get_brand_guidelines(
                organization_id,
            )

        return RAGContext(
            query=query,
            results=results,
            context_text=context_text,
            source_node_ids=[r.node_id for r in results],
            brand_guidelines=brand_guidelines,
            memory_context=memory_ctx,
            organization_id=str(organization_id),
            agent_id=agent_id,
        )

    async def ingest_brand_guidelines(
        self,
        organization_id: UUID,
        guidelines_text: str,
        *,
        name: str = "Brand Guidelines",
        properties: dict[str, Any] | None = None,
        user_id: UUID | None = None,
    ) -> IngestionResult:
        """Ingest brand guidelines into knowledge graph."""
        start = time.time()
        result = IngestionResult()

        try:
            # Create brand guideline node via existing service
            node_data = await self._ks.create_node(
                organization_id=organization_id,
                type=NodeType.BRAND,
                name=name,
                description=guidelines_text[:2000],
                properties={**(properties or {}), "category": "brand_guidelines"},
            )
            result.nodes_created += 1

            # Store corresponding memory
            if user_id:
                await self._ms.remember(
                    organization_id=organization_id,
                    user_id=user_id,
                    key=f"brand_guidelines_{name}",
                    value=guidelines_text[:500],
                    type="fact",
                    importance="high",
                )
                result.memories_created += 1

            # Publish event
            await EventBus.publish(DomainEvent.create(
                event_type=DomainEventType.CONTENT_CREATED,
                aggregate_id=node_data.get("id", ""),
                aggregate_type="knowledge_node",
                data={"type": "brand_guidelines", "name": name},
            ))

        except Exception as exc:
            result.errors.append(f"Brand guideline ingestion failed: {exc}")
            logger.exception("Brand guideline ingestion failed")

        result.processing_time_ms = (time.time() - start) * 1000
        return result

    async def ingest_campaign_data(
        self,
        organization_id: UUID,
        campaign_id: UUID,
        campaign_name: str,
        data: dict[str, Any],
        *,
        user_id: UUID | None = None,
    ) -> IngestionResult:
        """Ingest campaign metrics and insights into knowledge graph."""
        start = time.time()
        result = IngestionResult()

        try:
            # Index campaign as node (creates or updates)
            await self._ks.index_campaign(
                organization_id=organization_id,
                campaign_id=campaign_id,
                name=campaign_name,
                description=f"Campaign metrics: {str(data)[:500]}",
            )
            result.nodes_created += 1

            # Store as memory for recall
            if user_id:
                await self._ms.remember(
                    organization_id=organization_id,
                    user_id=user_id,
                    key=f"campaign_metrics_{campaign_id}",
                    value=f"{campaign_name}: {str(data)[:500]}",
                    type="insight",
                    importance="high",
                )
                result.memories_created += 1

        except Exception as exc:
            result.errors.append(f"Campaign data ingestion failed: {exc}")
            logger.exception("Campaign data ingestion failed")

        result.processing_time_ms = (time.time() - start) * 1000
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _vector_search(
        self,
        query: str,
        organization_id: UUID,
        *,
        type_filter: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Vector similarity search via existing KnowledgeGraphService."""
        try:
            raw = await self._ks.search(
                organization_id=organization_id,
                query=query,
                type_filter=type_filter,
                limit=limit,
            )
            return [
                SearchResult(
                    node_id=r["id"],
                    node_type=r.get("type", ""),
                    name=r.get("name", ""),
                    description=r.get("description", ""),
                    score=r.get("similarity", 0.5),
                    source="vector",
                    properties=r.get("properties", {}),
                )
                for r in raw
            ]
        except Exception:
            logger.debug("Vector search failed")
            return []

    async def _keyword_search(
        self,
        query: str,
        organization_id: UUID,
        *,
        type_filter: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Keyword-based search using extracted keywords."""
        keywords = self._extract_keywords(query)
        results: list[SearchResult] = []

        for keyword in keywords[:5]:  # limit keyword iterations
            try:
                raw = await self._ks.search(
                    organization_id=organization_id,
                    query=keyword,
                    type_filter=type_filter,
                    limit=limit,
                )
                for r in raw:
                    score = self._keyword_score(keyword, r)
                    results.append(SearchResult(
                        node_id=r["id"],
                        node_type=r.get("type", ""),
                        name=r.get("name", ""),
                        description=r.get("description", ""),
                        score=score,
                        source="keyword",
                        properties=r.get("properties", {}),
                    ))
            except Exception:
                continue

        return results

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query, removing stop words."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        return [w for w in words if w not in _STOP_WORDS]

    def _keyword_score(self, keyword: str, raw_node: dict) -> float:
        """Calculate keyword relevance score for a raw node dict."""
        text = f"{raw_node.get('name', '')} {raw_node.get('description', '')}".lower()
        count = text.count(keyword.lower())
        if count == 0:
            return 0.0
        return min(0.5 + (count * 0.1), 0.9)

    def _merge_results(
        self,
        vector_results: list[SearchResult],
        keyword_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Merge and deduplicate results from different search strategies."""
        seen: dict[str, SearchResult] = {}

        # Vector results take priority
        for r in vector_results:
            seen[r.node_id] = r

        # Merge keyword results
        for r in keyword_results:
            if r.node_id in seen:
                existing = seen[r.node_id]
                # Weighted average: vector gets 60%, keyword gets 40%
                existing.score = existing.score * 0.6 + r.score * 0.4
                existing.source = "combined"
            else:
                seen[r.node_id] = r

        return list(seen.values())

    async def _boost_with_graph_context(
        self,
        results: list[SearchResult],
    ) -> list[SearchResult]:
        """Boost scores based on graph connections (well-connected nodes rank higher)."""
        for r in results:
            try:
                node_uuid = UUID(r.node_id)
                relations = await self._ks.get_node_relations(node_uuid)
                r.related_node_ids = [
                    rel.get("source_id", "") if rel.get("target_id") == r.node_id
                    else rel.get("target_id", "")
                    for rel in relations
                ]
                # Boost for well-connected nodes
                boost = min(len(relations) * 0.02, 0.1)
                r.score = min(r.score + boost, 1.0)
            except Exception:
                pass
        return results

    async def _get_brand_guidelines(
        self,
        organization_id: UUID,
    ) -> str | None:
        """Fetch brand guidelines from knowledge graph."""
        try:
            raw = await self._ks.search(
                organization_id=organization_id,
                query="brand guidelines voice tone",
                type_filter="brand",
                limit=3,
            )
            if raw:
                return raw[0].get("description", "")
        except Exception:
            pass
        return None
