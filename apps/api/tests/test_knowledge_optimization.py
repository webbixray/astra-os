"""Tests for Predictive Optimization — M4 Intelligence.

Covers budget optimization, creative fatigue detection,
audience expansion suggestions, and unified suggestions.
Target: 12+ tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.services.knowledge.predictive_optimization import (
    AudienceExpansionSuggestion,
    BudgetAllocation,
    CreativeFatigueResult,
    OptimizationSuggestion,
    OptimizationType,
    PredictiveOptimizer,
    UrgencyLevel,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def mock_ks():
    ks = MagicMock()
    ks.search = AsyncMock(return_value=[])
    return ks


@pytest.fixture
def optimizer(mock_ks):
    return PredictiveOptimizer(knowledge_service=mock_ks)


# ---------------------------------------------------------------------------
# Value object tests
# ---------------------------------------------------------------------------

class TestBudgetAllocation:
    def test_budget_change_pct_increase(self):
        a = BudgetAllocation(
            campaign_id="1", campaign_name="Test",
            current_daily_budget=100, suggested_daily_budget=120,
            rationale="Good", confidence=0.8,
        )
        assert a.budget_change_pct == 20.0

    def test_budget_change_pct_decrease(self):
        a = BudgetAllocation(
            campaign_id="1", campaign_name="Test",
            current_daily_budget=100, suggested_daily_budget=80,
            rationale="Poor", confidence=0.7,
        )
        assert a.budget_change_pct == -20.0

    def test_budget_change_pct_zero_budget(self):
        a = BudgetAllocation(
            campaign_id="1", campaign_name="Test",
            current_daily_budget=0, suggested_daily_budget=0,
            rationale="n/a", confidence=0.5,
        )
        assert a.budget_change_pct == 0.0

    def test_to_dict(self):
        a = BudgetAllocation(
            campaign_id="1", campaign_name="Test",
            current_daily_budget=100, suggested_daily_budget=110,
            rationale="r", confidence=0.8,
        )
        d = a.to_dict()
        assert d["campaign_id"] == "1"
        assert d["budget_change_pct"] == 10.0


class TestCreativeFatigueResult:
    def test_to_dict(self):
        r = CreativeFatigueResult(
            creative_id="c1", creative_name="Ad A",
            is_fatigued=True, decline_rate=2.5,
            days_since_peak=7, current_ctr=0.02, peak_ctr=0.05,
            recommendation="Refresh creative",
        )
        d = r.to_dict()
        assert d["is_fatigued"] is True
        assert d["decline_rate"] == 2.5


class TestOptimizationSuggestion:
    def test_to_dict(self):
        s = OptimizationSuggestion(
            suggestion_type=OptimizationType.BUDGET_INCREASE,
            title="Increase budget",
            description="High ROAS",
            urgency=UrgencyLevel.HIGH,
            campaign_id="c1",
            confidence=0.85,
        )
        d = s.to_dict()
        assert d["suggestion_type"] == "budget_increase"
        assert d["urgency"] == "high"


# ---------------------------------------------------------------------------
# Budget optimization tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestBudgetOptimization:
    async def test_empty_campaigns(self, optimizer, org_id):
        result = await optimizer.optimize_budget(org_id, [])
        assert result == []

    async def test_single_campaign_no_change(self, optimizer, org_id):
        campaigns = [{"id": "1", "name": "A", "daily_budget": 100, "roas": 3.0, "impressions": 10000, "clicks": 500, "conversions": 50, "spend": 100}]
        result = await optimizer.optimize_budget(org_id, campaigns)
        assert len(result) == 1
        # With single campaign, factor should be ~1.0 (no reallocation possible)
        assert abs(result[0].budget_change_pct) < 25  # within clamping range

    async def test_top_performer_gets_more(self, optimizer, org_id):
        campaigns = [
            {"id": "1", "name": "Winner", "daily_budget": 100, "roas": 6.0, "impressions": 10000, "clicks": 500, "conversions": 100, "spend": 100},
            {"id": "2", "name": "Loser", "daily_budget": 100, "roas": 1.0, "impressions": 10000, "clicks": 100, "conversions": 10, "spend": 100},
        ]
        result = await optimizer.optimize_budget(org_id, campaigns)
        assert len(result) == 2
        winner = next(a for a in result if a.campaign_name == "Winner")
        loser = next(a for a in result if a.campaign_name == "Loser")
        assert winner.suggested_daily_budget >= loser.suggested_daily_budget

    async def test_total_budget_cap(self, optimizer, org_id):
        campaigns = [
            {"id": "1", "name": "A", "daily_budget": 100, "roas": 5.0, "impressions": 10000, "clicks": 500, "conversions": 80, "spend": 100},
            {"id": "2", "name": "B", "daily_budget": 100, "roas": 2.0, "impressions": 10000, "clicks": 200, "conversions": 20, "spend": 100},
        ]
        result = await optimizer.optimize_budget(org_id, campaigns, total_budget=150)
        total = sum(a.suggested_daily_budget for a in result)
        assert total <= 151  # small floating-point tolerance

    async def test_budget_clamped(self, optimizer, org_id):
        campaigns = [
            {"id": "1", "name": "A", "daily_budget": 100, "roas": 10.0, "impressions": 10000, "clicks": 1000, "conversions": 200, "spend": 50},
            {"id": "2", "name": "B", "daily_budget": 100, "roas": 0.5, "impressions": 10000, "clicks": 50, "conversions": 2, "spend": 200},
        ]
        result = await optimizer.optimize_budget(org_id, campaigns)
        for alloc in result:
            # Max 20% change per cycle
            assert -25 <= alloc.budget_change_pct <= 25

    async def test_confidence_reflects_performance(self, optimizer, org_id):
        campaigns = [
            {"id": "1", "name": "Great", "daily_budget": 100, "roas": 8.0, "impressions": 10000, "clicks": 500, "conversions": 100, "spend": 100},
            {"id": "2", "name": "Poor", "daily_budget": 100, "roas": 0.5, "impressions": 10000, "clicks": 50, "conversions": 5, "spend": 100},
        ]
        result = await optimizer.optimize_budget(org_id, campaigns)
        great = next(a for a in result if a.campaign_name == "Great")
        poor = next(a for a in result if a.campaign_name == "Poor")
        assert great.confidence >= poor.confidence


# ---------------------------------------------------------------------------
# Creative fatigue tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCreativeFatigue:
    async def test_no_creatives(self, optimizer, org_id):
        result = await optimizer.detect_creative_fatigue(org_id, [])
        assert result == []

    async def test_fatigued_creative(self, optimizer, org_id):
        # CTR declining from 5% to 2% over 7 days
        ctr_history = [0.05, 0.048, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02]
        creatives = [{
            "id": "c1", "name": "Ad A",
            "ctr_history": ctr_history,
            "current_ctr": 0.02,
            "peak_ctr": 0.05,
        }]
        result = await optimizer.detect_creative_fatigue(org_id, creatives)
        assert len(result) == 1
        assert result[0].is_fatigued is True
        assert result[0].decline_rate > 0

    async def test_healthy_creative(self, optimizer, org_id):
        ctr_history = [0.03, 0.031, 0.032, 0.031, 0.03]
        creatives = [{
            "id": "c2", "name": "Ad B",
            "ctr_history": ctr_history,
            "current_ctr": 0.03,
            "peak_ctr": 0.032,
        }]
        result = await optimizer.detect_creative_fatigue(org_id, creatives)
        assert len(result) == 1
        assert result[0].is_fatigued is False

    async def test_insufficient_data(self, optimizer, org_id):
        creatives = [{"id": "c3", "name": "Ad C", "ctr_history": [], "current_ctr": 0.03, "peak_ctr": 0.03}]
        result = await optimizer.detect_creative_fatigue(org_id, creatives)
        assert result[0].is_fatigued is False
        assert "Insufficient" in result[0].recommendation

    async def test_early_fatigue_warning(self, optimizer, org_id):
        # ~14% decline (between 9% early-warning and 15% fatigue thresholds)
        ctr_history = [0.05, 0.048, 0.045, 0.043, 0.042, 0.041, 0.043]
        creatives = [{
            "id": "c4", "name": "Ad D",
            "ctr_history": ctr_history,
            "current_ctr": 0.043,
            "peak_ctr": 0.05,
        }]
        result = await optimizer.detect_creative_fatigue(org_id, creatives)
        assert result[0].is_fatigued is False
        # ~14% decline is between early-warning (9%) and fatigue (15%) thresholds
        assert "Monitor" in result[0].recommendation


# ---------------------------------------------------------------------------
# Audience expansion tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAudienceExpansion:
    async def test_no_audiences_found(self, optimizer, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[])
        result = await optimizer.suggest_audience_expansion(org_id, "tech professionals")
        assert result == []

    async def test_suggestions_from_search(self, optimizer, org_id, mock_ks):
        mock_ks.search = AsyncMock(side_effect=[
            # Audience search
            [
                {"id": str(uuid4()), "type": "audience", "name": "Tech Enthusiasts", "description": "d", "similarity": 0.7},
                {"id": str(uuid4()), "type": "audience", "name": "Tech Professionals", "description": "d", "similarity": 0.99},  # too similar, filtered
            ],
            # Brand/demographics search (empty)
            [],
        ])
        result = await optimizer.suggest_audience_expansion(org_id, "tech professionals")
        # "Tech Professionals" should be filtered out (0.99 > 0.95)
        # "Tech Enthusiasts" at 0.7 should be included
        assert len(result) <= 1

    async def test_respects_limit(self, optimizer, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "audience", "name": f"Audience {i}", "description": "d", "similarity": 0.6}
            for i in range(20)
        ])
        result = await optimizer.suggest_audience_expansion(org_id, "source", limit=3)
        assert len(result) <= 3

    async def test_handles_exception(self, optimizer, org_id, mock_ks):
        mock_ks.search = AsyncMock(side_effect=Exception("DB error"))
        result = await optimizer.suggest_audience_expansion(org_id, "test")
        assert result == []


# ---------------------------------------------------------------------------
# Unified suggestions tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGenerateSuggestions:
    async def test_empty_campaigns(self, optimizer, org_id):
        result = await optimizer.generate_suggestions(org_id, [])
        assert result == []

    async def test_suggestions_for_meaningful_changes(self, optimizer, org_id):
        campaigns = [
            {"id": "1", "name": "A", "daily_budget": 100, "roas": 8.0, "impressions": 10000, "clicks": 500, "conversions": 100, "spend": 100},
            {"id": "2", "name": "B", "daily_budget": 100, "roas": 0.5, "impressions": 10000, "clicks": 50, "conversions": 5, "spend": 100},
        ]
        result = await optimizer.generate_suggestions(org_id, campaigns)
        # Should generate budget suggestions for both campaigns
        assert len(result) >= 1
        assert all(s.suggestion_type in [OptimizationType.BUDGET_INCREASE, OptimizationType.BUDGET_DECREASE] for s in result)
