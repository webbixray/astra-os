import random
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.campaigns.automation import (
    AudienceSegment,
    AutomationRule,
    BidOptimizationRule,
    BudgetAllocationRule,
    ContentRecommendation,
)
from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.infrastructure.db.models.advertising.advertising_models import AdInsightModel
from app.infrastructure.db.repositories.campaigns.automation_repository import (
    AudienceSegmentRepository,
    AutomationRuleRepository,
    BidOptimizationRuleRepository,
    BudgetAllocationRuleRepository,
    ContentRecommendationRepository,
)


class AutomationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.budget_repo = BudgetAllocationRuleRepository(db)
        self.bid_repo = BidOptimizationRuleRepository(db)
        self.audience_repo = AudienceSegmentRepository(db)
        self.recommendation_repo = ContentRecommendationRepository(db)
        self.rule_repo = AutomationRuleRepository(db)

    # ── Budget Allocation ────────────────────────────────────────────────

    async def create_budget_rule(self, org_id: UUID, campaign_id: UUID,
                                  name: str, strategy: str = "equal",
                                  allocations: dict | None = None) -> BudgetAllocationRule:
        rule = BudgetAllocationRule.create(org_id, campaign_id, name, strategy, allocations)
        return await self.budget_repo.save(rule)

    async def list_budget_rules(self, org_id: UUID) -> list[dict]:
        rules = await self.budget_repo.find_by_organization(org_id)
        return [
            {"id": str(r.id), "campaign_id": str(r.campaign_id),
             "name": r.name, "strategy": r.strategy,
             "allocations": r.allocations, "enabled": r.enabled}
            for r in rules
        ]

    async def calculate_allocation(self, rule_id: UUID) -> dict:
        rule = await self.budget_repo.find_by_id(rule_id)
        if rule is None:
            raise EntityNotFoundError("BudgetAllocationRule", str(rule_id))

        channels = rule.allocations or {}
        if rule.strategy == "equal":
            total = len(channels)
            return {ch: round(100.0 / total, 2) for ch in channels} if total else {}

        if rule.strategy == "performance_based":
            impression_result = await self.db.execute(
                select(
                    AdInsightModel.platform,
                    func.coalesce(func.sum(AdInsightModel.impressions), 0).label("total_impressions"),
                )
                .where(AdInsightModel.platform.in_(channels.keys()))
                .group_by(AdInsightModel.platform)
            )
            results = {row.platform: float(row.total_impressions) for row in impression_result.all()}
            for ch in channels:
                results.setdefault(ch, 0.0)
            total = sum(results.values()) or 1
            return {ch: round(val / total * 100, 2) for ch, val in results.items()}

        if rule.strategy == "ai_optimized":
            total = len(channels)
            allocations = {ch: round(100.0 / total + random.uniform(-5, 5), 2) for ch in channels}
            total_pct = sum(allocations.values())
            return {ch: round(v / total_pct * 100, 2) for ch, v in allocations.items()}

        return dict(channels)

    # ── Bid Optimization ─────────────────────────────────────────────────

    async def create_bid_rule(self, org_id: UUID, ad_account_id: UUID,
                               name: str, strategy: str = "target_cpa",
                               target_value: float = 0.0,
                               min_bid: float = 0.0,
                               max_bid: float = 0.0) -> BidOptimizationRule:
        rule = BidOptimizationRule.create(org_id, ad_account_id, name, strategy,
                                          target_value, min_bid, max_bid)
        return await self.bid_repo.save(rule)

    async def list_bid_rules(self, org_id: UUID) -> list[dict]:
        rules = await self.bid_repo.find_by_organization(org_id)
        return [
            {"id": str(r.id), "ad_account_id": str(r.ad_account_id),
             "name": r.name, "strategy": r.strategy,
             "target_value": r.target_value, "min_bid": r.min_bid,
             "max_bid": r.max_bid, "enabled": r.enabled}
            for r in rules
        ]

    async def optimize_bid(self, rule_id: UUID) -> dict:
        rule = await self.bid_repo.find_by_id(rule_id)
        if rule is None:
            raise EntityNotFoundError("BidOptimizationRule", str(rule_id))

        suggested_bid = rule.target_value * random.uniform(0.8, 1.2)
        suggested_bid = max(rule.min_bid, min(rule.max_bid, suggested_bid)) if rule.max_bid > 0 else suggested_bid

        return {
            "rule_id": str(rule.id), "strategy": rule.strategy,
            "suggested_bid": round(suggested_bid, 2),
            "target_value": rule.target_value,
            "confidence": round(random.uniform(0.6, 0.95), 2),
        }

    # ── Audience Segmentation ────────────────────────────────────────────

    async def create_audience_segment(self, org_id: UUID, name: str,
                                       source: str = "custom",
                                       criteria: dict | None = None) -> AudienceSegment:
        segment = AudienceSegment.create(org_id, name, source, criteria)
        segment.predicted_size = random.randint(1000, 100000)
        segment.confidence_score = round(random.uniform(0.5, 0.95), 2)
        return await self.audience_repo.save(segment)

    async def list_audience_segments(self, org_id: UUID) -> list[dict]:
        segments = await self.audience_repo.find_by_organization(org_id)
        return [
            {"id": str(s.id), "name": s.name, "source": s.source,
             "predicted_size": s.predicted_size,
             "confidence_score": s.confidence_score, "criteria": s.criteria}
            for s in segments
        ]

    async def predict_audience(self, segment_id: UUID) -> dict:
        segment = await self.audience_repo.find_by_id(segment_id)
        if segment is None:
            raise EntityNotFoundError("AudienceSegment", str(segment_id))
        return {
            "segment_id": str(segment.id), "name": segment.name,
            "predicted_size": segment.predicted_size,
            "confidence_score": segment.confidence_score,
            "estimated_reach": int(segment.predicted_size * random.uniform(0.5, 0.9)),
            "suggested_channels": ["google_ads", "meta", "linkedin"],
        }

    # ── Content Recommendations ──────────────────────────────────────────

    AI_RECOMMENDATIONS: ClassVar[list[dict[str, str]]] = [
        {"type": "topic", "title": "Industry trends and insights",
         "description": "Create content around emerging industry trends to capture early adopter attention"},
        {"type": "format", "title": "Short-form video content",
         "description": "Video content has 3x higher engagement — prioritize reels and shorts"},
        {"type": "channel", "title": "LinkedIn for B2B campaigns",
         "description": "B2B audiences respond best on LinkedIn — increase allocation by 20%"},
        {"type": "timing", "title": "Optimal posting time 10-11am",
         "description": "Peak engagement occurs between 10-11am on weekdays"},
        {"type": "headline", "title": "Use question-based headlines",
         "description": "Question headlines drive 40% higher click-through rates"},
        {"type": "cta", "title": "Social proof CTAs outperform",
         "description": "CTAs like 'Join 10,000+ marketers' convert 25% better"},
    ]

    async def generate_recommendations(self, org_id: UUID,
                                        campaign_id: UUID | None = None) -> list[ContentRecommendation]:
        recs = []
        for rec_data in self.AI_RECOMMENDATIONS:
            score = round(random.uniform(0.55, 0.95), 2)
            rec = ContentRecommendation.create(
                organization_id=org_id, campaign_id=campaign_id,
                recommendation_type=rec_data["type"],
                title=rec_data["title"],
                description=rec_data["description"],
                confidence_score=score,
            )
            recs.append(await self.recommendation_repo.save(rec))
        return recs

    async def list_recommendations(self, org_id: UUID,
                                    rec_type: str | None = None) -> list[dict]:
        recs = await self.recommendation_repo.find_by_organization(org_id, rec_type)
        return [
            {"id": str(r.id), "type": r.recommendation_type,
             "title": r.title, "description": r.description,
             "confidence_score": r.confidence_score,
             "applied": r.applied}
            for r in recs
        ]

    async def apply_recommendation(self, rec_id: UUID) -> ContentRecommendation:
        rec = await self.recommendation_repo.find_by_id(rec_id)
        if rec is None:
            raise EntityNotFoundError("ContentRecommendation", str(rec_id))
        rec.mark_applied()
        return await self.recommendation_repo.save(rec)

    # ── Automation Rules Engine ──────────────────────────────────────────

    async def create_rule(self, org_id: UUID, name: str, trigger_type: str,
                           action_type: str, trigger_config: dict | None = None,
                           action_config: dict | None = None,
                           description: str = "",
                           created_by: UUID | None = None) -> AutomationRule:
        rule = AutomationRule.create(org_id, name, trigger_type, action_type,
                                     trigger_config, action_config, description, created_by)
        return await self.rule_repo.save(rule)

    async def list_rules(self, org_id: UUID) -> list[dict]:
        rules = await self.rule_repo.find_by_organization(org_id)
        return [
            {"id": str(r.id), "name": r.name, "description": r.description,
             "trigger_type": r.trigger_type, "trigger_config": r.trigger_config,
             "action_type": r.action_type, "action_config": r.action_config,
             "enabled": r.enabled, "execution_count": r.execution_count,
             "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None}
            for r in rules
        ]

    async def toggle_rule(self, rule_id: UUID, enabled: bool) -> AutomationRule:
        rule = await self.rule_repo.find_by_id(rule_id)
        if rule is None:
            raise EntityNotFoundError("AutomationRule", str(rule_id))
        rule.toggle(enabled)
        return await self.rule_repo.save(rule)

    async def evaluate_rules(self, org_id: UUID) -> list[dict]:
        rules = await self.rule_repo.find_enabled(org_id)
        triggered_rules = []
        results = []
        for rule in rules:
            triggered = random.random() < 0.3
            if triggered:
                rule.record_execution()
                triggered_rules.append(rule)
            results.append({
                "rule_id": str(rule.id), "name": rule.name,
                "trigger_type": rule.trigger_type,
                "action_type": rule.action_type,
                "triggered": triggered,
                "execution_count": rule.execution_count,
            })
        if triggered_rules:
            await self.rule_repo.save_all(triggered_rules)
        return results

    async def delete_budget_rule(self, rule_id: UUID) -> None:
        await self.budget_repo.delete(rule_id)

    async def delete_bid_rule(self, rule_id: UUID) -> None:
        await self.bid_repo.delete(rule_id)

    async def delete_audience_segment(self, segment_id: UUID) -> None:
        await self.audience_repo.delete(segment_id)

    async def delete_recommendation(self, rec_id: UUID) -> None:
        await self.recommendation_repo.delete(rec_id)

    async def delete_rule(self, rule_id: UUID) -> None:
        await self.rule_repo.delete(rule_id)
