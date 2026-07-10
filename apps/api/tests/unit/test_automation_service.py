from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.campaigns.automation_service import AutomationService
from app.domain.entities.campaigns.automation import (
    AudienceSegment,
    AutomationRule,
    BidOptimizationRule,
    BudgetAllocationRule,
    ContentRecommendation,
)
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    s = AutomationService.__new__(AutomationService)
    s.db = MagicMock()
    s.db.execute = AsyncMock()
    s.budget_repo = MagicMock()
    s.bid_repo = MagicMock()
    s.audience_repo = MagicMock()
    s.recommendation_repo = MagicMock()
    s.rule_repo = MagicMock()
    return s


class TestBudgetRules:
    async def test_create_budget_rule(self, service):
        service.budget_repo.save = AsyncMock(return_value=BudgetAllocationRule(
            id=uuid4(), name="Budget Rule",
        ))

        result = await service.create_budget_rule(uuid4(), uuid4(), "Budget Rule")

        assert result.name == "Budget Rule"

    async def test_list_budget_rules(self, service):
        r = MagicMock(spec=BudgetAllocationRule)
        r.id = uuid4()
        r.campaign_id = uuid4()
        r.name = "Rule"
        r.strategy = "equal"
        r.allocations = {"social": 50}
        r.enabled = True
        service.budget_repo.find_by_organization = AsyncMock(return_value=[r])

        result = await service.list_budget_rules(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Rule"

    async def test_calculate_allocation_equal(self, service):
        rule = MagicMock(spec=BudgetAllocationRule)
        rule.strategy = "equal"
        rule.allocations = {"social": 100, "search": 200}
        service.budget_repo.find_by_id = AsyncMock(return_value=rule)

        result = await service.calculate_allocation(uuid4())

        assert result["social"] == 50.0
        assert result["search"] == 50.0

    async def test_calculate_allocation_not_found(self, service):
        service.budget_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.calculate_allocation(uuid4())

    async def test_calculate_allocation_performance_based(self, service):
        rule = MagicMock(spec=BudgetAllocationRule)
        rule.strategy = "performance_based"
        rule.allocations = {"google": 100, "meta": 200}
        service.budget_repo.find_by_id = AsyncMock(return_value=rule)

        imp_result = MagicMock()
        imp_result.scalar.return_value = 1000
        service.db.execute = AsyncMock(return_value=imp_result)

        result = await service.calculate_allocation(uuid4())

        assert "google" in result
        assert "meta" in result

    async def test_calculate_allocation_ai_optimized(self, service):
        rule = MagicMock(spec=BudgetAllocationRule)
        rule.strategy = "ai_optimized"
        rule.allocations = {"social": 100, "search": 200}
        service.budget_repo.find_by_id = AsyncMock(return_value=rule)

        with patch("app.application.use_cases.campaigns.automation_service.random.uniform", return_value=0):
            result = await service.calculate_allocation(uuid4())

        assert len(result) == 2
        assert abs(sum(result.values()) - 100.0) < 0.1

    async def test_calculate_allocation_unknown_strategy(self, service):
        rule = MagicMock(spec=BudgetAllocationRule)
        rule.strategy = "manual"
        rule.allocations = {"social": 100, "search": 200}
        service.budget_repo.find_by_id = AsyncMock(return_value=rule)

        result = await service.calculate_allocation(uuid4())

        assert result == {"social": 100, "search": 200}

    async def test_delete_budget_rule(self, service):
        service.budget_repo.delete = AsyncMock()

        await service.delete_budget_rule(uuid4())

        service.budget_repo.delete.assert_awaited_once()


class TestBidRules:
    async def test_create_bid_rule(self, service):
        service.bid_repo.save = AsyncMock(return_value=BidOptimizationRule(
            id=uuid4(), name="Bid Rule",
        ))

        result = await service.create_bid_rule(uuid4(), uuid4(), "Bid Rule")

        assert result.name == "Bid Rule"

    async def test_list_bid_rules(self, service):
        r = MagicMock(spec=BidOptimizationRule)
        r.id = uuid4()
        r.ad_account_id = uuid4()
        r.name = "Rule"
        r.strategy = "target_cpa"
        r.target_value = 5.0
        r.min_bid = 1.0
        r.max_bid = 10.0
        r.enabled = True
        service.bid_repo.find_by_organization = AsyncMock(return_value=[r])

        result = await service.list_bid_rules(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Rule"

    async def test_optimize_bid(self, service):
        rule = MagicMock(spec=BidOptimizationRule)
        rule.id = uuid4()
        rule.strategy = "target_cpa"
        rule.target_value = 5.0
        rule.min_bid = 1.0
        rule.max_bid = 10.0
        service.bid_repo.find_by_id = AsyncMock(return_value=rule)

        with patch("app.application.use_cases.campaigns.automation_service.random.uniform", return_value=1.0):
            result = await service.optimize_bid(uuid4())

        assert result["suggested_bid"] == 5.0
        assert result["strategy"] == "target_cpa"

    async def test_optimize_bid_not_found(self, service):
        service.bid_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.optimize_bid(uuid4())

    async def test_delete_bid_rule(self, service):
        service.bid_repo.delete = AsyncMock()

        await service.delete_bid_rule(uuid4())

        service.bid_repo.delete.assert_awaited_once()


class TestAudienceSegments:
    async def test_create_audience_segment(self, service):
        service.audience_repo.save = AsyncMock(return_value=AudienceSegment(
            id=uuid4(), name="Segment",
        ))

        result = await service.create_audience_segment(uuid4(), "Segment")

        assert result.name == "Segment"

    async def test_list_audience_segments(self, service):
        s = MagicMock(spec=AudienceSegment)
        s.id = uuid4()
        s.name = "Segment"
        s.source = "custom"
        s.predicted_size = 50000
        s.confidence_score = 0.85
        s.criteria = {"age": "18-35"}
        service.audience_repo.find_by_organization = AsyncMock(return_value=[s])

        result = await service.list_audience_segments(uuid4())

        assert len(result) == 1
        assert result[0]["predicted_size"] == 50000

    async def test_predict_audience(self, service):
        seg = MagicMock(spec=AudienceSegment)
        seg.id = uuid4()
        seg.name = "Segment"
        seg.predicted_size = 50000
        seg.confidence_score = 0.85
        service.audience_repo.find_by_id = AsyncMock(return_value=seg)

        result = await service.predict_audience(uuid4())

        assert result["name"] == "Segment"
        assert "suggested_channels" in result

    async def test_predict_audience_not_found(self, service):
        service.audience_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.predict_audience(uuid4())

    async def test_delete_audience_segment(self, service):
        service.audience_repo.delete = AsyncMock()

        await service.delete_audience_segment(uuid4())

        service.audience_repo.delete.assert_awaited_once()


class TestContentRecommendations:
    async def test_generate_recommendations(self, service):
        service.recommendation_repo.save = AsyncMock(side_effect=lambda r: r)

        result = await service.generate_recommendations(uuid4())

        assert len(result) == 6

    async def test_list_recommendations(self, service):
        r = MagicMock(spec=ContentRecommendation)
        r.id = uuid4()
        r.recommendation_type = "topic"
        r.title = "Industry trends"
        r.description = "Create content"
        r.confidence_score = 0.85
        r.applied = False
        service.recommendation_repo.find_by_organization = AsyncMock(return_value=[r])

        result = await service.list_recommendations(uuid4())

        assert len(result) == 1
        assert result[0]["title"] == "Industry trends"

    async def test_apply_recommendation(self, service):
        rec = MagicMock(spec=ContentRecommendation)
        rec.id = uuid4()
        rec.mark_applied = MagicMock()
        service.recommendation_repo.find_by_id = AsyncMock(return_value=rec)
        service.recommendation_repo.save = AsyncMock(return_value=rec)

        await service.apply_recommendation(uuid4())

        rec.mark_applied.assert_called_once()

    async def test_apply_recommendation_not_found(self, service):
        service.recommendation_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.apply_recommendation(uuid4())

    async def test_delete_recommendation(self, service):
        service.recommendation_repo.delete = AsyncMock()

        await service.delete_recommendation(uuid4())

        service.recommendation_repo.delete.assert_awaited_once()


class TestAutomationRules:
    async def test_create_rule(self, service):
        service.rule_repo.save = AsyncMock(return_value=AutomationRule(
            id=uuid4(), name="Rule",
        ))

        result = await service.create_rule(uuid4(), "Rule", "schedule", "adjust_budget")

        assert result.name == "Rule"

    async def test_list_rules(self, service):
        r = MagicMock(spec=AutomationRule)
        r.id = uuid4()
        r.name = "Rule"
        r.description = "desc"
        r.trigger_type = "schedule"
        r.trigger_config = {}
        r.action_type = "email"
        r.action_config = {}
        r.enabled = True
        r.execution_count = 5
        r.last_triggered_at = None
        service.rule_repo.find_by_organization = AsyncMock(return_value=[r])

        result = await service.list_rules(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Rule"

    async def test_toggle_rule(self, service):
        rule = MagicMock(spec=AutomationRule)
        rule.toggle = MagicMock()
        service.rule_repo.find_by_id = AsyncMock(return_value=rule)
        service.rule_repo.save = AsyncMock(return_value=rule)

        await service.toggle_rule(uuid4(), True)

        rule.toggle.assert_called_with(True)

    async def test_toggle_rule_not_found(self, service):
        service.rule_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.toggle_rule(uuid4(), True)

    async def test_evaluate_rules(self, service):
        rule = MagicMock(spec=AutomationRule)
        rule.id = uuid4()
        rule.name = "Rule"
        rule.trigger_type = "schedule"
        rule.action_type = "email"
        rule.execution_count = 0
        rule.record_execution = MagicMock()
        service.rule_repo.find_enabled = AsyncMock(return_value=[rule])
        service.rule_repo.save_all = AsyncMock()

        with patch("app.application.use_cases.campaigns.automation_service.random.random", return_value=0.1):
            result = await service.evaluate_rules(uuid4())

        assert len(result) == 1
        assert result[0]["triggered"] is True
        rule.record_execution.assert_called_once()

    async def test_evaluate_rules_not_triggered(self, service):
        rule = MagicMock(spec=AutomationRule)
        rule.id = uuid4()
        rule.name = "Rule"
        rule.trigger_type = "schedule"
        rule.action_type = "email"
        service.rule_repo.find_enabled = AsyncMock(return_value=[rule])

        with patch("app.application.use_cases.campaigns.automation_service.random.random", return_value=0.9):
            result = await service.evaluate_rules(uuid4())

        assert result[0]["triggered"] is False

    async def test_delete_rule(self, service):
        service.rule_repo.delete = AsyncMock()

        await service.delete_rule(uuid4())

        service.rule_repo.delete.assert_awaited_once()
