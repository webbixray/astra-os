"""Predictive Optimization — Budget allocation, creative fatigue, audience expansion.

M4 Intelligence: Analyzes campaign data from the knowledge graph to provide
optimization suggestions. Stateless service that operates on structured data.

Builds on existing KnowledgeGraphService + MemoryService.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from app.application.use_cases.knowledge.knowledge_service import (
    KnowledgeGraphService,
)
from app.domain.entities.knowledge.node import NodeType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

class OptimizationType(str, Enum):
    BUDGET_REALLOCATION = "budget_reallocation"
    CREATIVE_FATIGUE = "creative_fatigue"
    AUDIENCE_EXPANSION = "audience_expansion"
    BUDGET_INCREASE = "budget_increase"
    BUDGET_DECREASE = "budget_decrease"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OptimizationSuggestion:
    """A single optimization recommendation."""

    suggestion_type: OptimizationType
    title: str
    description: str
    urgency: UrgencyLevel
    campaign_id: str | None = None
    confidence: float = 0.0  # 0.0–1.0
    estimated_impact: str = ""
    action_items: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_type": self.suggestion_type.value,
            "title": self.title,
            "description": self.description,
            "urgency": self.urgency.value,
            "campaign_id": self.campaign_id,
            "confidence": self.confidence,
            "estimated_impact": self.estimated_impact,
            "action_items": self.action_items,
            "metadata": self.metadata,
        }


@dataclass
class BudgetAllocation:
    """Optimized budget allocation for a campaign."""

    campaign_id: str
    campaign_name: str
    current_daily_budget: float
    suggested_daily_budget: float
    rationale: str
    confidence: float = 0.0

    @property
    def budget_change_pct(self) -> float:
        if self.current_daily_budget == 0:
            return 0.0
        return (
            (self.suggested_daily_budget - self.current_daily_budget)
            / self.current_daily_budget
            * 100
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "current_daily_budget": self.current_daily_budget,
            "suggested_daily_budget": self.suggested_daily_budget,
            "budget_change_pct": round(self.budget_change_pct, 1),
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


@dataclass
class CreativeFatigueResult:
    """Creative fatigue analysis for a single creative."""

    creative_id: str
    creative_name: str
    is_fatigued: bool
    decline_rate: float  # % decline per day
    days_since_peak: int
    current_ctr: float
    peak_ctr: float
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "creative_id": self.creative_id,
            "creative_name": self.creative_name,
            "is_fatigued": self.is_fatigued,
            "decline_rate": round(self.decline_rate, 2),
            "days_since_peak": self.days_since_peak,
            "current_ctr": round(self.current_ctr, 4),
            "peak_ctr": round(self.peak_ctr, 4),
            "recommendation": self.recommendation,
        }


@dataclass
class AudienceExpansionSuggestion:
    """Suggested audience expansion based on knowledge graph analysis."""

    source_audience: str
    suggested_audience: str
    overlap_estimate: float  # 0.0–1.0
    rationale: str
    confidence: float = 0.0
    related_node_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_audience": self.source_audience,
            "suggested_audience": self.suggested_audience,
            "overlap_estimate": round(self.overlap_estimate, 2),
            "rationale": self.rationale,
            "confidence": self.confidence,
            "related_node_ids": self.related_node_ids,
        }


# ---------------------------------------------------------------------------
# Predictive Optimizer
# ---------------------------------------------------------------------------

# Thresholds for optimization heuristics
_ROAS_LOW_THRESHOLD = 2.0
_ROAS_HIGH_THRESHOLD = 5.0
_CTR_FATIGUE_DECLINE_PCT = 15.0  # % decline from peak → fatigue
_BUDGET_SCALE_FACTOR = 0.2  # Max 20% increase/decrease per cycle
_AUDIENCE_CONFIDENCE_MIN = 0.4


class PredictiveOptimizer:
    """Stateless service that provides optimization suggestions.

    Analyzes campaign data stored in the knowledge graph and produces
    actionable recommendations for budget, creative, and audience optimization.
    """

    def __init__(self, knowledge_service: KnowledgeGraphService) -> None:
        self._ks = knowledge_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def optimize_budget(
        self,
        organization_id: UUID,
        campaigns: list[dict[str, Any]],
        total_budget: float | None = None,
    ) -> list[BudgetAllocation]:
        """Suggest budget reallocation across campaigns based on performance.

        Each campaign dict should include:
            - id, name, daily_budget, roas (return on ad spend)
            - impressions, clicks, conversions, spend
        """
        if not campaigns:
            return []

        allocations: list[BudgetAllocation] = []

        # Calculate performance scores
        scored = []
        for c in campaigns:
            roas = float(c.get("roas", 0))
            spend = float(c.get("spend", 0))
            conversions = float(c.get("conversions", 0))
            impressions = float(c.get("impressions", 0))

            # Composite score: ROAS (40%) + conversion rate (30%) + efficiency (30%)
            conv_rate = conversions / impressions if impressions > 0 else 0
            cost_per_conv = spend / conversions if conversions > 0 else float("inf")
            efficiency = 1.0 / (1.0 + cost_per_conv) if cost_per_conv < float("inf") else 0

            score = (roas * 0.4) + (conv_rate * 100 * 0.3) + (efficiency * 0.3)
            scored.append((c, score))

        # Sort by performance score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Reallocate: top performers get more, bottom get less
        avg_score = sum(s for _, s in scored) / len(scored) if scored else 1.0

        for campaign, score in scored:
            current = float(campaign.get("daily_budget", 0))
            name = campaign.get("name", "Unknown")
            cid = str(campaign.get("id", ""))

            if avg_score == 0:
                factor = 1.0
            else:
                factor = score / avg_score

            # Clamp to ±20% change
            factor = max(1.0 - _BUDGET_SCALE_FACTOR, min(factor, 1.0 + _BUDGET_SCALE_FACTOR))

            suggested = round(current * factor, 2)

            # Determine rationale
            roas = float(campaign.get("roas", 0))
            if roas >= _ROAS_HIGH_THRESHOLD:
                rationale = f"Strong ROAS ({roas:.1f}x) — increase budget to capture more conversions."
                confidence = min(0.7 + (roas - _ROAS_HIGH_THRESHOLD) * 0.05, 0.95)
            elif roas <= _ROAS_LOW_THRESHOLD and roas > 0:
                rationale = f"Low ROAS ({roas:.1f}x) — reduce spend and reallocate to top performers."
                confidence = min(0.6 + (_ROAS_LOW_THRESHOLD - roas) * 0.05, 0.9)
            else:
                rationale = f"Moderate performance (score {score:.2f}) — maintain or adjust slightly."
                confidence = 0.5

            allocations.append(BudgetAllocation(
                campaign_id=cid,
                campaign_name=name,
                current_daily_budget=current,
                suggested_daily_budget=suggested,
                rationale=rationale,
                confidence=round(confidence, 2),
            ))

        # Enforce total budget cap if provided
        if total_budget is not None:
            total_suggested = sum(a.suggested_daily_budget for a in allocations)
            if total_suggested > total_budget:
                ratio = total_budget / total_suggested
                for a in allocations:
                    a.suggested_daily_budget = round(a.suggested_daily_budget * ratio, 2)

        return allocations

    async def detect_creative_fatigue(
        self,
        organization_id: UUID,
        creatives: list[dict[str, Any]],
    ) -> list[CreativeFatigueResult]:
        """Detect creative fatigue from performance time series.

        Each creative dict should include:
            - id, name
            - ctr_history: list of daily CTR values (newest last)
            - current_ctr, peak_ctr, peak_day_index
        """
        results: list[CreativeFatigueResult] = []

        for creative in creatives:
            name = creative.get("name", "Unknown")
            cid = str(creative.get("id", ""))
            ctr_history = creative.get("ctr_history", [])
            current_ctr = float(creative.get("current_ctr", 0))
            peak_ctr = float(creative.get("peak_ctr", 0))

            if not ctr_history or peak_ctr == 0:
                results.append(CreativeFatigueResult(
                    creative_id=cid,
                    creative_name=name,
                    is_fatigued=False,
                    decline_rate=0.0,
                    days_since_peak=0,
                    current_ctr=current_ctr,
                    peak_ctr=peak_ctr,
                    recommendation="Insufficient data for fatigue analysis.",
                ))
                continue

            # Find peak and calculate decline rate
            peak_idx = ctr_history.index(max(ctr_history)) if ctr_history else 0
            days_since_peak = len(ctr_history) - 1 - peak_idx

            if peak_ctr > 0:
                decline_pct = (peak_ctr - current_ctr) / peak_ctr * 100
            else:
                decline_pct = 0.0

            decline_per_day = decline_pct / max(days_since_peak, 1)

            is_fatigued = decline_pct >= _CTR_FATIGUE_DECLINE_PCT and days_since_peak >= 3

            if is_fatigued:
                recommendation = (
                    f"Creative fatigue detected: {decline_pct:.0f}% CTR decline over "
                    f"{days_since_peak} days. Recommend refreshing creative or "
                    f"rotating to new variant."
                )
            elif decline_pct >= _CTR_FATIGUE_DECLINE_PCT * 0.6:
                recommendation = (
                    f"Early fatigue signs: {decline_pct:.0f}% CTR decline. "
                    f"Monitor closely and prepare new creative."
                )
            else:
                recommendation = "Creative performing within normal range."

            results.append(CreativeFatigueResult(
                creative_id=cid,
                creative_name=name,
                is_fatigued=is_fatigued,
                decline_rate=decline_per_day,
                days_since_peak=days_since_peak,
                current_ctr=current_ctr,
                peak_ctr=peak_ctr,
                recommendation=recommendation,
            ))

        return results

    async def suggest_audience_expansion(
        self,
        organization_id: UUID,
        source_audience: str,
        campaign_id: UUID | None = None,
        limit: int = 5,
    ) -> list[AudienceExpansionSuggestion]:
        """Suggest audience expansions based on knowledge graph connections.

        Searches the knowledge graph for audiences related to the source
        audience and suggests expansion targets.
        """
        suggestions: list[AudienceExpansionSuggestion] = []

        try:
            # Search for related audiences in the knowledge graph
            raw = await self._ks.search(
                organization_id=organization_id,
                query=source_audience,
                type_filter="audience",
                limit=limit + 5,  # fetch extra for filtering
            )

            for node in raw:
                node_name = node.get("name", "")
                # Skip the source audience itself
                if node_name.lower() == source_audience.lower():
                    continue

                # Calculate overlap estimate from similarity
                similarity = node.get("similarity", 0.5)
                # Higher similarity = more overlap, lower = more unique reach
                overlap_estimate = similarity

                # Only suggest audiences with moderate overlap
                # (too similar = redundant, too different = irrelevant)
                if overlap_estimate < 0.2 or overlap_estimate > 0.95:
                    continue

                confidence = min(0.5 + similarity * 0.3, 0.9)

                suggestions.append(AudienceExpansionSuggestion(
                    source_audience=source_audience,
                    suggested_audience=node_name,
                    overlap_estimate=overlap_estimate,
                    rationale=(
                        f"Related audience '{node_name}' shares ~{overlap_estimate:.0%} "
                        f"characteristics with '{source_audience}'. Expanding to this "
                        f"audience can reach adjacent segments with similar conversion "
                        f"potential."
                    ),
                    confidence=round(confidence, 2),
                    related_node_ids=[node.get("id", "")],
                ))

        except Exception:
            logger.exception("Audience expansion suggestion failed")

        # Also look at related nodes via graph traversal
        try:
            raw_brand = await self._ks.search(
                organization_id=organization_id,
                query=f"{source_audience} target audience demographics",
                limit=limit,
            )
            seen_names = {s.suggested_audience.lower() for s in suggestions}
            for node in raw_brand:
                node_name = node.get("name", "")
                if (
                    node_name.lower() not in seen_names
                    and node_name.lower() != source_audience.lower()
                ):
                    similarity = node.get("similarity", 0.3)
                    if similarity >= _AUDIENCE_CONFIDENCE_MIN:
                        suggestions.append(AudienceExpansionSuggestion(
                            source_audience=source_audience,
                            suggested_audience=node_name,
                            overlap_estimate=similarity * 0.8,
                            rationale=(
                                f"Knowledge graph link suggests '{node_name}' is "
                                f"adjacent to '{source_audience}'."
                            ),
                            confidence=round(similarity * 0.6, 2),
                            related_node_ids=[node.get("id", "")],
                        ))
        except Exception:
            pass

        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:limit]

    async def generate_suggestions(
        self,
        organization_id: UUID,
        campaign_data: list[dict[str, Any]],
    ) -> list[OptimizationSuggestion]:
        """Generate a unified list of optimization suggestions across all dimensions."""
        suggestions: list[OptimizationSuggestion] = []

        # Budget optimization
        allocations = await self.optimize_budget(organization_id, campaign_data)
        for alloc in allocations:
            change_pct = alloc.budget_change_pct
            if abs(change_pct) >= 5:  # Only suggest meaningful changes
                opt_type = (
                    OptimizationType.BUDGET_INCREASE
                    if change_pct > 0
                    else OptimizationType.BUDGET_DECREASE
                )
                suggestions.append(OptimizationSuggestion(
                    suggestion_type=opt_type,
                    title=f"{'Increase' if change_pct > 0 else 'Decrease'} budget for {alloc.campaign_name}",
                    description=alloc.rationale,
                    urgency=(
                        UrgencyLevel.HIGH if abs(change_pct) >= 15
                        else UrgencyLevel.MEDIUM
                    ),
                    campaign_id=alloc.campaign_id,
                    confidence=alloc.confidence,
                    estimated_impact=f"{change_pct:+.1f}% budget change",
                    action_items=[
                        f"Adjust daily budget from ${alloc.current_daily_budget} to ${alloc.suggested_daily_budget}"
                    ],
                ))

        return suggestions
