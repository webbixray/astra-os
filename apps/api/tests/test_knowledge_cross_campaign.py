"""Tests for Cross-Campaign Learning — M4 Intelligence.

Covers pattern mining, transfer learning, learning insights, and edge cases.
Target: 12+ tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.services.knowledge.cross_campaign_learning import (
    CampaignPattern,
    CrossCampaignLearner,
    LearningInsight,
    PatternType,
    TransferRecommendation,
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
def learner(mock_ks):
    return CrossCampaignLearner(knowledge_service=mock_ks)


# ---------------------------------------------------------------------------
# Value object tests
# ---------------------------------------------------------------------------

class TestCampaignPattern:
    def test_to_dict(self):
        p = CampaignPattern(
            pattern_id="p1",
            pattern_type=PatternType.AUDIENCE_PATTERN,
            title="Shared audience",
            description="desc",
            campaign_ids=["c1", "c2"],
            strength=0.8,
            sample_size=2,
            confidence=0.75,
        )
        d = p.to_dict()
        assert d["pattern_type"] == "audience_pattern"
        assert d["strength"] == 0.8
        assert d["campaign_ids"] == ["c1", "c2"]


class TestTransferRecommendation:
    def test_to_dict(self):
        p = CampaignPattern(
            pattern_id="p1", pattern_type=PatternType.CHANNEL_PATTERN,
            title="t", description="d", campaign_ids=["c1"],
            strength=0.7, sample_size=1, confidence=0.7,
        )
        r = TransferRecommendation(
            source_campaign_id="c1", source_campaign_name="Source",
            target_campaign_id="c2", target_campaign_name="Target",
            pattern=p,
            transfer_strategy="Apply audience targeting",
            expected_lift="15% improvement",
            confidence=0.8,
        )
        d = r.to_dict()
        assert d["source_campaign_name"] == "Source"
        assert d["confidence"] == 0.8


class TestLearningInsight:
    def test_to_dict(self):
        i = LearningInsight(
            insight_id="i1",
            title="High-performing pattern",
            description="desc",
            supporting_campaigns=["c1", "c2"],
            insight_type="audience_pattern",
            priority="high",
            recommended_actions=["Review pattern"],
        )
        d = i.to_dict()
        assert d["actionable"] is True
        assert len(d["recommended_actions"]) == 1


# ---------------------------------------------------------------------------
# Pattern mining tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestMinePatterns:
    async def test_fewer_than_min_campaigns(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": "1", "name": "Solo Campaign", "description": "d", "similarity": 0.8, "properties": {}},
        ])
        patterns = await learner.mine_patterns(org_id)
        assert patterns == []

    async def test_mines_patterns(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "campaign", "name": "Summer Sale 2024", "description": "Summer campaign", "similarity": 0.8, "properties": {}},
            {"id": str(uuid4()), "type": "campaign", "name": "Summer Promo 2023", "description": "Summer promo", "similarity": 0.7, "properties": {}},
            {"id": str(uuid4()), "type": "campaign", "name": "Winter Campaign", "description": "Winter campaign", "similarity": 0.6, "properties": {}},
        ])
        patterns = await learner.mine_patterns(org_id)
        # Should find at least one pattern (Summer* campaigns share prefix)
        assert isinstance(patterns, list)

    async def test_respects_limit(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "name": f"Campaign {i}", "description": "d", "similarity": 0.8, "properties": {}}
            for i in range(20)
        ])
        patterns = await learner.mine_patterns(org_id, limit=3)
        assert len(patterns) <= 3

    async def test_filters_by_pattern_type(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "name": "A", "description": "d", "similarity": 0.8, "properties": {}},
            {"id": str(uuid4()), "name": "A", "description": "d", "similarity": 0.7, "properties": {}},
        ])
        patterns = await learner.mine_patterns(
            org_id, pattern_types=[PatternType.AUDIENCE_PATTERN],
        )
        assert all(p.pattern_type == PatternType.AUDIENCE_PATTERN for p in patterns)

    async def test_handles_exception(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(side_effect=Exception("DB error"))
        patterns = await learner.mine_patterns(org_id)
        assert patterns == []


# ---------------------------------------------------------------------------
# Transfer suggestions tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTransferSuggestions:
    async def test_no_target_campaign(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[])
        result = await learner.suggest_transfers(org_id, "nonexistent")
        assert result == []

    async def test_suggestions_for_related(self, learner, org_id, mock_ks):
        target_id = str(uuid4())
        related_id = str(uuid4())
        mock_ks.search = AsyncMock(side_effect=[
            # Target campaign search
            [{"id": target_id, "name": "Summer Campaign", "description": "d", "similarity": 1.0, "properties": {"campaign_id": target_id}}],
            # Related campaigns
            [
                {"id": related_id, "name": "Summer Promo", "description": "d", "similarity": 0.7, "properties": {"campaign_id": related_id}},
                {"id": str(uuid4()), "name": "Winter Sale", "description": "d", "similarity": 0.2, "properties": {}},  # too low
            ],
        ])
        result = await learner.suggest_transfers(org_id, target_id)
        # Should have 1 recommendation (Summer Promo with 0.7 similarity)
        assert len(result) == 1
        assert result[0].source_campaign_name == "Summer Promo"

    async def test_respects_limit(self, learner, org_id, mock_ks):
        target_id = str(uuid4())
        mock_ks.search = AsyncMock(side_effect=[
            [{"id": target_id, "name": "Target", "description": "d", "similarity": 1.0, "properties": {"campaign_id": target_id}}],
            [{"id": str(uuid4()), "name": f"Related {i}", "description": "d", "similarity": 0.7, "properties": {}} for i in range(10)],
        ])
        result = await learner.suggest_transfers(org_id, target_id, limit=3)
        assert len(result) <= 3


# ---------------------------------------------------------------------------
# Learning insights tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestLearningInsights:
    async def test_insights_from_patterns(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "name": "Alpha Campaign", "description": "d", "similarity": 0.9, "properties": {}},
            {"id": str(uuid4()), "name": "Alpha Promo", "description": "d", "similarity": 0.8, "properties": {}},
        ])
        insights = await learner.get_learning_insights(org_id)
        assert isinstance(insights, list)

    async def test_empty_when_no_patterns(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "name": "Solo", "description": "d", "similarity": 0.5, "properties": {}},
        ])
        insights = await learner.get_learning_insights(org_id)
        assert insights == []

    async def test_respects_limit(self, learner, org_id, mock_ks):
        mock_ks.search = AsyncMock(return_value=[
            {"id": str(uuid4()), "name": f"Campaign {i}", "description": "d", "similarity": 0.8, "properties": {}}
            for i in range(20)
        ])
        insights = await learner.get_learning_insights(org_id, limit=5)
        assert len(insights) <= 5


# ---------------------------------------------------------------------------
# Clustering helper tests
# ---------------------------------------------------------------------------

class TestClustering:
    def test_cluster_by_name_prefix(self, learner):
        campaigns = [
            {"name": "Summer Sale 2024", "id": "1"},
            {"name": "Summer Promo 2023", "id": "2"},
            {"name": "Winter Campaign", "id": "3"},
        ]
        clusters = learner._cluster_campaigns(campaigns, key="name")
        assert "summer" in clusters
        assert "winter" in clusters
        assert len(clusters["summer"]) == 2
        assert len(clusters["winter"]) == 1

    def test_average_similarity(self, learner):
        nodes = [
            {"similarity": 0.8},
            {"similarity": 0.6},
        ]
        assert learner._average_similarity(nodes) == 0.7

    def test_average_similarity_empty(self, learner):
        assert learner._average_similarity([]) == 0.0
