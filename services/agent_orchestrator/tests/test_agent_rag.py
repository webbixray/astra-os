"""Tests for Agent RAG integration — M4 Intelligence.

Tests the new set_rag_pipeline, get_rag_context, and search_knowledge
methods added to the Agent base class.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.domain.services.knowledge.rag_pipeline import (
    RAGContext,
    RagPipeline,
    SearchResult,
)
from services.agent import (
    Agent,
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentType,
)

# ---------------------------------------------------------------------------
# Concrete agent for testing
# ---------------------------------------------------------------------------

class DummyAgent(Agent):
    """Minimal concrete agent for testing RAG integration."""

    async def execute(self, context: AgentContext, input_data) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            success=True,
            output={"done": True},
        )

    async def reason(self, context: AgentContext, observation) -> Any:
        return observation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent():
    config = AgentConfig(
        agent_id=uuid4(),
        agent_type=AgentType.CONTENT_SPECIALIST,
        name="Test Agent",
        description="A test agent",
    )
    return DummyAgent(config, tenant_id=uuid4())


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock(spec=RagPipeline)
    pipeline.search = AsyncMock(return_value=[])
    pipeline.assemble_context = AsyncMock(return_value=RAGContext(
        query="test", results=[], context_text="No context",
        source_node_ids=[],
    ))
    return pipeline


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAgentRAGIntegration:
    def test_no_pipeline_by_default(self, agent):
        """Agent should have no RAG pipeline by default."""
        assert agent._rag_pipeline is None

    def test_set_rag_pipeline(self, agent, mock_pipeline):
        """set_rag_pipeline should store the pipeline."""
        agent.set_rag_pipeline(mock_pipeline)
        assert agent._rag_pipeline is mock_pipeline

    @pytest.mark.asyncio
    async def test_get_rag_context_without_pipeline(self, agent):
        """get_rag_context should return None when no pipeline is set."""
        result = await agent.get_rag_context("test", uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_rag_context_with_pipeline(self, agent, mock_pipeline):
        """get_rag_context should delegate to the pipeline."""
        agent.set_rag_pipeline(mock_pipeline)
        ctx = await agent.get_rag_context("test query", uuid4())
        mock_pipeline.assemble_context.assert_called_once()
        assert ctx is not None

    @pytest.mark.asyncio
    async def test_get_rag_context_handles_exception(self, agent, mock_pipeline):
        """get_rag_context should return None on error."""
        mock_pipeline.assemble_context = AsyncMock(side_effect=Exception("DB error"))
        agent.set_rag_pipeline(mock_pipeline)
        result = await agent.get_rag_context("test", uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_search_knowledge_without_pipeline(self, agent):
        """search_knowledge should return empty list when no pipeline."""
        results = await agent.search_knowledge("test", uuid4())
        assert results == []

    @pytest.mark.asyncio
    async def test_search_knowledge_with_pipeline(self, agent, mock_pipeline):
        """search_knowledge should delegate to pipeline and format results."""
        mock_pipeline.search = AsyncMock(return_value=[
            SearchResult(
                node_id=str(uuid4()), node_type="campaign",
                name="Test Node", description="A test node description",
                score=0.85, source="vector", properties={},
            ),
        ])
        agent.set_rag_pipeline(mock_pipeline)
        results = await agent.search_knowledge("test query", uuid4(), limit=5)
        assert len(results) == 1
        assert results[0]["name"] == "Test Node"
        assert results[0]["relevance"] == "high"

    @pytest.mark.asyncio
    async def test_search_knowledge_handles_exception(self, agent, mock_pipeline):
        """search_knowledge should return empty list on error."""
        mock_pipeline.search = AsyncMock(side_effect=Exception("Network error"))
        agent.set_rag_pipeline(mock_pipeline)
        results = await agent.search_knowledge("test", uuid4())
        assert results == []

    @pytest.mark.asyncio
    async def test_search_knowledge_respects_limit(self, agent, mock_pipeline):
        """search_knowledge should pass limit to pipeline."""
        mock_pipeline.search = AsyncMock(return_value=[])
        agent.set_rag_pipeline(mock_pipeline)
        await agent.search_knowledge("test", uuid4(), limit=3)
        mock_pipeline.search.assert_called_once_with(
            query="test",
            organization_id=mock_pipeline.search.call_args[1].get("organization_id") or mock_pipeline.search.call_args[0][1],
            limit=3,
        )
