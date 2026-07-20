"""Integration tests for knowledge M4 API routes.

Tests the RAG, optimization, and cross-campaign learning endpoints
using mocked FastAPI dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.services.knowledge.cross_campaign_learning import (
    CampaignPattern,
    LearningInsight,
    PatternType,
)
from app.domain.services.knowledge.predictive_optimization import (
    BudgetAllocation,
    CreativeFatigueResult,
)
from app.domain.services.knowledge.rag_pipeline import (
    IngestionResult,
    RAGContext,
    SearchResult,
)
from app.presentation.routes.knowledge.cross_campaign_routes import router as cc_router
from app.presentation.routes.knowledge.optimization_routes import router as opt_router
from app.presentation.routes.knowledge.rag_routes import router as rag_router

# ---------------------------------------------------------------------------
# Mock dependencies
# ---------------------------------------------------------------------------

_mock_user_id = uuid4()


async def mock_require_user_id() -> uuid4:
    return _mock_user_id


def create_test_app() -> FastAPI:
    app = FastAPI()
    # Override auth dependency globally
    app.dependency_overrides[rag_router.__module__ and None] = None  # no-op

    # We'll override at the function level
    return app


# Instead of overriding the dependency via the router, we patch the
# module-level functions that resolve dependencies.


@pytest.fixture
def org_id():
    return str(uuid4())


@pytest.fixture
def client():
    """Create a test client with mocked auth and DB dependencies."""
    app = FastAPI()
    app.include_router(rag_router)
    app.include_router(opt_router)
    app.include_router(cc_router)

    # Override auth — patch at the function import location
    import app.presentation.routes.knowledge.cross_campaign_routes as cc_mod
    import app.presentation.routes.knowledge.optimization_routes as opt_mod
    import app.presentation.routes.knowledge.rag_routes as rag_mod

    app.dependency_overrides[rag_mod.require_user_id] = lambda: _mock_user_id
    app.dependency_overrides[opt_mod.require_user_id] = lambda: _mock_user_id
    app.dependency_overrides[cc_mod.require_user_id] = lambda: _mock_user_id

    # Override get_db — we don't actually need a DB since we patch pipelines
    app.dependency_overrides[rag_mod.get_db] = lambda: None
    app.dependency_overrides[opt_mod.get_db] = lambda: None
    app.dependency_overrides[cc_mod.get_db] = lambda: None

    # Override pipeline dependencies
    mock_pipeline = MagicMock()
    app.dependency_overrides[rag_mod.get_rag_pipeline] = lambda: mock_pipeline

    mock_optimizer = MagicMock()
    app.dependency_overrides[opt_mod.get_optimizer] = lambda: mock_optimizer

    mock_learner = MagicMock()
    app.dependency_overrides[cc_mod.get_learner] = lambda: mock_learner

    return TestClient(app), mock_pipeline, mock_optimizer, mock_learner


# ---------------------------------------------------------------------------
# RAG Routes
# ---------------------------------------------------------------------------


class TestRAGRoutes:
    def test_search_empty(self, client, org_id):
        c, mock_pipeline, _, _ = client
        mock_pipeline.search = AsyncMock(return_value=[])

        resp = c.post(
            "/knowledge/rag/search",
            json={
                "organization_id": org_id,
                "query": "test",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
        assert data["total"] == 0

    def test_search_with_results(self, client, org_id):
        c, mock_pipeline, _, _ = client
        mock_pipeline.search = AsyncMock(
            return_value=[
                SearchResult(
                    node_id=str(uuid4()),
                    node_type="campaign",
                    name="Summer Sale",
                    description="A great campaign",
                    score=0.9,
                    source="vector",
                    properties={},
                ),
            ]
        )

        resp = c.post(
            "/knowledge/rag/search",
            json={
                "organization_id": org_id,
                "query": "summer",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "Summer Sale"

    def test_context_assembly(self, client, org_id):
        c, mock_pipeline, _, _ = client
        mock_pipeline.assemble_context = AsyncMock(
            return_value=RAGContext(
                query="test",
                results=[],
                context_text="No context",
                source_node_ids=[],
                organization_id=org_id,
            )
        )

        resp = c.post(
            "/knowledge/rag/context",
            json={
                "organization_id": org_id,
                "query": "test",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["context_text"] == "No context"

    def test_ingest_brand_guidelines(self, client, org_id):
        c, mock_pipeline, _, _ = client
        mock_pipeline.ingest_brand_guidelines = AsyncMock(
            return_value=IngestionResult(
                nodes_created=1,
                memories_created=1,
                processing_time_ms=42.5,
            )
        )

        resp = c.post(
            "/knowledge/rag/ingest/brand-guidelines",
            json={
                "organization_id": org_id,
                "guidelines_text": "Use clean design",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["nodes_created"] == 1

    def test_ingest_campaign_data(self, client, org_id):
        c, mock_pipeline, _, _ = client
        mock_pipeline.ingest_campaign_data = AsyncMock(
            return_value=IngestionResult(
                nodes_created=1,
                processing_time_ms=10.0,
            )
        )

        resp = c.post(
            "/knowledge/rag/ingest/campaign-data",
            json={
                "organization_id": org_id,
                "campaign_id": str(uuid4()),
                "campaign_name": "Test Campaign",
                "data": {"roas": 3.5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# Optimization Routes
# ---------------------------------------------------------------------------


class TestOptimizationRoutes:
    def test_budget_optimization(self, client, org_id):
        c, _, mock_optimizer, _ = client
        mock_optimizer.optimize_budget = AsyncMock(
            return_value=[
                BudgetAllocation(
                    campaign_id="1",
                    campaign_name="A",
                    current_daily_budget=100,
                    suggested_daily_budget=120,
                    rationale="Strong ROAS",
                    confidence=0.8,
                ),
            ]
        )

        resp = c.post(
            "/knowledge/optimization/budget",
            json={
                "organization_id": org_id,
                "campaigns": [
                    {
                        "id": "1",
                        "name": "A",
                        "daily_budget": 100,
                        "roas": 5.0,
                        "impressions": 10000,
                        "clicks": 500,
                        "conversions": 80,
                        "spend": 100,
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["allocations"]) == 1
        assert data["allocations"][0]["budget_change_pct"] == 20.0

    def test_creative_fatigue(self, client, org_id):
        c, _, mock_optimizer, _ = client
        mock_optimizer.detect_creative_fatigue = AsyncMock(
            return_value=[
                CreativeFatigueResult(
                    creative_id="c1",
                    creative_name="Ad A",
                    is_fatigued=True,
                    decline_rate=2.5,
                    days_since_peak=7,
                    current_ctr=0.02,
                    peak_ctr=0.05,
                    recommendation="Refresh",
                ),
            ]
        )

        resp = c.post(
            "/knowledge/optimization/creative-fatigue",
            json={
                "organization_id": org_id,
                "creatives": [
                    {
                        "id": "c1",
                        "name": "Ad A",
                        "ctr_history": [0.05, 0.02],
                        "current_ctr": 0.02,
                        "peak_ctr": 0.05,
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fatigued_count"] == 1

    def test_audience_expansion(self, client, org_id):
        c, _, mock_optimizer, _ = client
        mock_optimizer.suggest_audience_expansion = AsyncMock(return_value=[])

        resp = c.post(
            "/knowledge/optimization/audience-expansion",
            json={
                "organization_id": org_id,
                "source_audience": "tech professionals",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_suggestions"] == 0

    def test_suggestions(self, client, org_id):
        c, _, mock_optimizer, _ = client
        mock_optimizer.generate_suggestions = AsyncMock(return_value=[])

        resp = c.post(
            "/knowledge/optimization/suggestions",
            json={
                "organization_id": org_id,
                "campaigns": [
                    {
                        "id": "1",
                        "name": "A",
                        "daily_budget": 100,
                        "roas": 3.0,
                        "impressions": 10000,
                        "clicks": 500,
                        "conversions": 50,
                        "spend": 100,
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# Cross-Campaign Routes
# ---------------------------------------------------------------------------


class TestCrossCampaignRoutes:
    def test_mine_patterns(self, client, org_id):
        c, _, _, mock_learner = client
        mock_learner.mine_patterns = AsyncMock(
            return_value=[
                CampaignPattern(
                    pattern_id="p1",
                    pattern_type=PatternType.AUDIENCE_PATTERN,
                    title="Shared audience",
                    description="desc",
                    campaign_ids=["c1", "c2"],
                    strength=0.8,
                    sample_size=2,
                    confidence=0.75,
                ),
            ]
        )

        resp = c.post(
            "/knowledge/patterns/mine",
            json={
                "organization_id": org_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["patterns"][0]["pattern_type"] == "audience_pattern"

    def test_transfer_suggestions(self, client, org_id):
        c, _, _, mock_learner = client
        mock_learner.suggest_transfers = AsyncMock(return_value=[])

        resp = c.post(
            "/knowledge/patterns/transfer",
            json={
                "organization_id": org_id,
                "target_campaign_id": "c1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_learning_insights(self, client, org_id):
        c, _, _, mock_learner = client
        mock_learner.get_learning_insights = AsyncMock(
            return_value=[
                LearningInsight(
                    insight_id="i1",
                    title="High-performing pattern",
                    description="desc",
                    supporting_campaigns=["c1"],
                    insight_type="audience_pattern",
                    priority="high",
                    recommended_actions=["Review"],
                ),
            ]
        )

        resp = c.post(
            "/knowledge/patterns/insights",
            json={
                "organization_id": org_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
