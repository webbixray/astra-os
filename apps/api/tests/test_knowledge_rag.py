"""Tests for RAG Pipeline — M4 Intelligence.

Covers hybrid search, context assembly, ingestion, and all edge cases.
Target: 15+ tests for the RAG pipeline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.services.knowledge.rag_pipeline import (
    IngestionResult,
    RAGContext,
    RagPipeline,
    SearchResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_ks():
    """Mock KnowledgeGraphService."""
    ks = MagicMock()
    ks.search = AsyncMock(return_value=[])
    ks.create_node = AsyncMock(return_value={"id": str(uuid4()), "type": "brand", "name": "Test"})
    ks.create_relation = AsyncMock(return_value={})
    ks.get_node_relations = AsyncMock(return_value=[])
    ks.index_campaign = AsyncMock(return_value=None)
    ks.index_content = AsyncMock(return_value=None)
    return ks


@pytest.fixture
def mock_ms():
    """Mock MemoryService."""
    ms = MagicMock()
    ms.remember = AsyncMock(return_value={"id": str(uuid4()), "key": "test", "type": "fact", "importance": "medium"})
    ms.recall = AsyncMock(return_value=[])
    ms.get_memories = AsyncMock(return_value=[])
    return ms


@pytest.fixture
def pipeline(mock_ks, mock_ms):
    return RagPipeline(
        knowledge_service=mock_ks,
        memory_service=mock_ms,
    )


# ---------------------------------------------------------------------------
# SearchResult tests
# ---------------------------------------------------------------------------

class TestSearchResult:
    def test_relevance_high(self):
        r = SearchResult(node_id="1", node_type="campaign", name="Test", description="d", score=0.9, source="vector")
        assert r.relevance_label == "high"

    def test_relevance_medium(self):
        r = SearchResult(node_id="1", node_type="campaign", name="Test", description="d", score=0.6, source="vector")
        assert r.relevance_label == "medium"

    def test_relevance_low(self):
        r = SearchResult(node_id="1", node_type="campaign", name="Test", description="d", score=0.2, source="vector")
        assert r.relevance_label == "low"

    def test_default_values(self):
        r = SearchResult(node_id="1", node_type="campaign", name="T", description="d", score=0.5, source="x")
        assert r.properties == {}
        assert r.related_node_ids == []


# ---------------------------------------------------------------------------
# IngestionResult tests
# ---------------------------------------------------------------------------

class TestIngestionResult:
    def test_success_when_no_errors(self):
        r = IngestionResult()
        assert r.success is True
        assert r.processing_time_ms == 0.0

    def test_failure_when_errors(self):
        r = IngestionResult(errors=["something failed"])
        assert r.success is False

    def test_to_dict(self):
        r = IngestionResult(nodes_created=1, processing_time_ms=42.5)
        d = r.to_dict()
        assert d["nodes_created"] == 1
        assert d["success"] is True
        assert d["processing_time_ms"] == 42.5


# ---------------------------------------------------------------------------
# RAGContext tests
# ---------------------------------------------------------------------------

class TestRAGContext:
    def test_result_count(self):
        results = [
            SearchResult(node_id=str(i), node_type="x", name="n", description="d", score=0.5, source="v")
            for i in range(5)
        ]
        ctx = RAGContext(query="test", results=results, context_text="ctx", source_node_ids=[])
        assert ctx.result_count == 5

    def test_high_relevance_count(self):
        results = [
            SearchResult(node_id="1", node_type="x", name="n", description="d", score=0.9, source="v"),
            SearchResult(node_id="2", node_type="x", name="n", description="d", score=0.5, source="v"),
        ]
        ctx = RAGContext(query="test", results=results, context_text="ctx", source_node_ids=[])
        assert ctx.high_relevance_count == 1


# ---------------------------------------------------------------------------
# RagPipeline.search tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRagPipelineSearch:
    async def test_search_empty_results(self, pipeline, org_id):
        results = await pipeline.search("nonexistent query", org_id)
        assert results == []

    async def test_search_vector_results(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "campaign", "name": "Campaign A", "description": "desc", "similarity": 0.9, "properties": {}},
        ])
        results = await pipeline.search("campaign", org_id)
        assert len(results) == 1
        # Both vector and keyword phases find the same node → merged as "combined"
        assert results[0].source == "combined"
        assert results[0].score >= 0.5

    async def test_search_merges_keyword_results(self, pipeline, org_id, mock_ks):
        node1_id = str(uuid4())
        node2_id = str(uuid4())

        # First call = vector search, second call = keyword search for each keyword
        mock_ks.search = AsyncMock(side_effect=[
            # vector search
            [{"id": node1_id, "type": "campaign", "name": "Summer Sale", "description": "summer campaign", "similarity": 0.8, "properties": {}}],
            # keyword search for "summer"
            [{"id": node1_id, "type": "campaign", "name": "Summer Sale", "description": "summer campaign", "similarity": 0.7, "properties": {}}],
            # keyword search for "sale"
            [{"id": node2_id, "type": "campaign", "name": "Flash Sale", "description": "quick sale", "similarity": 0.6, "properties": {}}],
        ])

        results = await pipeline.search("summer sale campaign", org_id, min_score=0.1)
        # Should have at least 1 result (node1 from vector, node2 from keyword)
        assert len(results) >= 1

    async def test_search_respects_type_filter(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "content", "name": "Blog", "description": "d", "similarity": 0.8, "properties": {}},
        ])
        await pipeline.search("blog", org_id, type_filter="content")
        # Type filter is passed to the knowledge service
        mock_ks.search.assert_called()

    async def test_search_respects_limit(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "x", "name": f"Node {i}", "description": "d", "similarity": 0.9 - i * 0.1, "properties": {}}
            for i in range(10)
        ])
        results = await pipeline.search("test", org_id, limit=3, min_score=0.0)
        assert len(results) <= 3

    async def test_search_filters_by_min_score(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "x", "name": "High", "description": "d", "similarity": 0.9, "properties": {}},
            {"id": str(uuid4()), "type": "x", "name": "Low", "description": "d", "similarity": 0.1, "properties": {}},
        ])
        results = await pipeline.search("test", org_id, min_score=0.5)
        # Low score result should be filtered
        assert all(r.score >= 0.5 for r in results)

    async def test_search_handles_exception_gracefully(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(side_effect=Exception("DB error"))
        results = await pipeline.search("test", org_id)
        assert results == []


# ---------------------------------------------------------------------------
# RagPipeline.assemble_context tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRagPipelineContext:
    async def test_assemble_context_no_results(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[])
        ctx = await pipeline.assemble_context("empty", org_id, include_memories=False)
        assert ctx.result_count == 0
        assert "No relevant context" in ctx.context_text

    async def test_assemble_context_with_results(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "campaign", "name": "Test Campaign", "description": "A great campaign", "similarity": 0.9, "properties": {}},
        ])
        ctx = await pipeline.assemble_context("test", org_id, include_memories=False)
        assert ctx.result_count >= 1
        assert "Test Campaign" in ctx.context_text

    async def test_assemble_context_includes_memories(self, pipeline, org_id, user_id, mock_ks, mock_ms):
        mock_ks.search = AsyncMock(return_value=[])
        mock_ms.recall = AsyncMock(return_value=[
            {"key": "preference", "value": "likes dark mode", "importance": "high"},
        ])
        ctx = await pipeline.assemble_context("test", org_id, user_id=user_id, include_memories=True)
        assert len(ctx.memory_context) == 1

    async def test_assemble_context_brand_guidelines(self, pipeline, org_id, mock_ks):
        # search() internally calls _vector_search + _keyword_search (each calls ks.search),
        # then _get_brand_guidelines calls ks.search again. Provide enough side_effects.
        brand_node = [{"id": str(uuid4()), "type": "brand", "name": "Brand Guide", "description": "Use blue color", "similarity": 0.8, "properties": {}}]
        empty = []
        mock_ks.search = AsyncMock(side_effect=[
            empty,  # vector search in search()
            empty,  # keyword search (each keyword) in search()
            brand_node,  # _get_brand_guidelines search
        ])
        ctx = await pipeline.assemble_context("test", org_id, include_brand_guidelines=True, include_memories=False)
        assert ctx.brand_guidelines == "Use blue color"

    async def test_assemble_context_no_brand_guidelines_when_disabled(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[])
        ctx = await pipeline.assemble_context("test", org_id, include_brand_guidelines=False, include_memories=False)
        assert ctx.brand_guidelines is None

    async def test_assemble_context_agent_id(self, pipeline, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[])
        ctx = await pipeline.assemble_context("test", org_id, agent_id="ceo_agent", include_memories=False)
        assert ctx.agent_id == "ceo_agent"


# ---------------------------------------------------------------------------
# RagPipeline.ingest tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRagPipelineIngestion:
    async def test_ingest_brand_guidelines_success(self, pipeline, org_id, mock_ks, mock_ms):
        result = await pipeline.ingest_brand_guidelines(
            org_id, "Use clean design", name="My Brand",
        )
        assert result.success
        assert result.nodes_created == 1
        mock_ks.create_node.assert_called_once()

    async def test_ingest_brand_guidelines_with_user(self, pipeline, org_id, user_id, mock_ks, mock_ms):
        result = await pipeline.ingest_brand_guidelines(
            org_id, "Guidelines text", user_id=user_id,
        )
        assert result.success
        assert result.memories_created == 1

    async def test_ingest_brand_guidelines_failure(self, pipeline, org_id, mock_ks):
        mock_ks.create_node = AsyncMock(side_effect=Exception("DB error"))
        result = await pipeline.ingest_brand_guidelines(org_id, "text")
        assert not result.success
        assert len(result.errors) == 1

    async def test_ingest_campaign_data_success(self, pipeline, org_id, mock_ks, mock_ms):
        cid = uuid4()
        result = await pipeline.ingest_campaign_data(
            org_id, cid, "Summer Campaign", {"roas": 3.5},
        )
        assert result.success
        mock_ks.index_campaign.assert_called_once()

    async def test_ingest_campaign_data_with_user(self, pipeline, org_id, user_id, mock_ks, mock_ms):
        cid = uuid4()
        result = await pipeline.ingest_campaign_data(
            org_id, cid, "Test", {"roas": 2.0}, user_id=user_id,
        )
        assert result.memories_created == 1

    async def test_ingest_campaign_data_failure(self, pipeline, org_id, mock_ks):
        mock_ks.index_campaign = AsyncMock(side_effect=Exception("DB error"))
        result = await pipeline.ingest_campaign_data(
            org_id, uuid4(), "Campaign", {},
        )
        assert not result.success


# ---------------------------------------------------------------------------
# Keyword extraction tests
# ---------------------------------------------------------------------------

class TestKeywordExtraction:
    def test_extracts_keywords(self, pipeline):
        keywords = pipeline._extract_keywords("What are the best performing campaigns?")
        assert "best" in keywords
        assert "performing" in keywords
        assert "campaigns" in keywords

    def test_removes_stop_words(self, pipeline):
        keywords = pipeline._extract_keywords("the quick brown fox is very fast")
        assert "the" not in keywords
        assert "is" not in keywords
        assert "quick" in keywords
        assert "brown" in keywords

    def test_short_words_removed(self, pipeline):
        keywords = pipeline._extract_keywords("my ad for fb")
        # "my", "ad", "for", "fb" are all < 3 chars
        assert keywords == []


# ---------------------------------------------------------------------------
# Merge results tests
# ---------------------------------------------------------------------------

class TestMergeResults:
    def test_merge_deduplicates(self, pipeline):
        nid = str(uuid4())
        v = SearchResult(node_id=nid, node_type="x", name="n", description="d", score=0.8, source="vector")
        k = SearchResult(node_id=nid, node_type="x", name="n", description="d", score=0.6, source="keyword")
        merged = pipeline._merge_results([v], [k])
        assert len(merged) == 1
        assert merged[0].source == "combined"
        # Weighted: 0.8*0.6 + 0.6*0.4 = 0.48 + 0.24 = 0.72
        assert abs(merged[0].score - 0.72) < 0.01

    def test_merge_keeps_unique(self, pipeline):
        v = SearchResult(node_id="1", node_type="x", name="n", description="d", score=0.8, source="vector")
        k = SearchResult(node_id="2", node_type="x", name="n", description="d", score=0.6, source="keyword")
        merged = pipeline._merge_results([v], [k])
        assert len(merged) == 2
