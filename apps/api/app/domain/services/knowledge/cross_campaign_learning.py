"""Cross-Campaign Learning — Pattern mining and transfer learning via knowledge graph.

M4 Intelligence: Discovers patterns across campaigns and transfers learnings
using the knowledge graph as a shared memory substrate.

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

class PatternType(str, Enum):
    AUDIENCE_PATTERN = "audience_pattern"
    CONTENT_PATTERN = "content_pattern"
    TIMING_PATTERN = "timing_pattern"
    CHANNEL_PATTERN = "channel_pattern"
    BUDGET_PATTERN = "budget_pattern"
    CREATIVE_PATTERN = "creative_pattern"


@dataclass
class CampaignPattern:
    """A discovered pattern across multiple campaigns."""

    pattern_id: str
    pattern_type: PatternType
    title: str
    description: str
    campaign_ids: list[str]
    strength: float  # 0.0–1.0 (how strong the pattern is)
    sample_size: int
    confidence: float  # 0.0–1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "title": self.title,
            "description": self.description,
            "campaign_ids": self.campaign_ids,
            "strength": round(self.strength, 2),
            "sample_size": self.sample_size,
            "confidence": round(self.confidence, 2),
            "metadata": self.metadata,
        }


@dataclass
class TransferRecommendation:
    """Recommendation to transfer a pattern from one campaign to another."""

    source_campaign_id: str
    source_campaign_name: str
    target_campaign_id: str
    target_campaign_name: str
    pattern: CampaignPattern
    transfer_strategy: str
    expected_lift: str
    confidence: float = 0.0
    prerequisites: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_campaign_id": self.source_campaign_id,
            "source_campaign_name": self.source_campaign_name,
            "target_campaign_id": self.target_campaign_id,
            "target_campaign_name": self.target_campaign_name,
            "pattern": self.pattern.to_dict(),
            "transfer_strategy": self.transfer_strategy,
            "expected_lift": self.expected_lift,
            "confidence": self.confidence,
            "prerequisites": self.prerequisites,
        }


@dataclass
class LearningInsight:
    """Aggregated learning insight from cross-campaign analysis."""

    insight_id: str
    title: str
    description: str
    supporting_campaigns: list[str]
    insight_type: str
    priority: str  # high, medium, low
    actionable: bool = True
    recommended_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "supporting_campaigns": self.supporting_campaigns,
            "insight_type": self.insight_type,
            "priority": self.priority,
            "actionable": self.actionable,
            "recommended_actions": self.recommended_actions,
        }


# ---------------------------------------------------------------------------
# Cross-Campaign Learner
# ---------------------------------------------------------------------------

_MIN_CAMPAIGNS_FOR_PATTERN = 2
_PATTERN_STRENGTH_THRESHOLD = 0.3
_TRANSFER_CONFIDENCE_MIN = 0.4


class CrossCampaignLearner:
    """Stateless service for cross-campaign learning via knowledge graph.

    Discovers patterns across campaigns and recommends transfer strategies
    using the knowledge graph as a shared memory substrate.
    """

    def __init__(self, knowledge_service: KnowledgeGraphService) -> None:
        self._ks = knowledge_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def mine_patterns(
        self,
        organization_id: UUID,
        campaign_ids: list[str] | None = None,
        pattern_types: list[PatternType] | None = None,
        limit: int = 10,
    ) -> list[CampaignPattern]:
        """Mine patterns across campaigns from the knowledge graph.

        Analyzes campaign nodes and their relationships to discover
        recurring patterns in audience, content, timing, channel, etc.
        """
        patterns: list[CampaignPattern] = []

        # Fetch campaign nodes from knowledge graph
        campaigns = await self._fetch_campaigns(organization_id, campaign_ids)

        if len(campaigns) < _MIN_CAMPAIGNS_FOR_PATTERN:
            return patterns

        # Mine each pattern type
        types_to_mine = pattern_types or list(PatternType)
        for ptype in types_to_mine:
            try:
                discovered = await self._mine_pattern_type(
                    organization_id, campaigns, ptype,
                )
                patterns.extend(discovered)
            except Exception:
                logger.debug("Pattern mining failed for %s", ptype.value)

        # Sort by strength * confidence
        patterns.sort(key=lambda p: p.strength * p.confidence, reverse=True)
        return patterns[:limit]

    async def suggest_transfers(
        self,
        organization_id: UUID,
        target_campaign_id: str,
        limit: int = 5,
    ) -> list[TransferRecommendation]:
        """Suggest transferring patterns from high-performing campaigns
        to a target campaign.

        Analyzes the target campaign, finds related campaigns in the
        knowledge graph, and recommends which patterns to transfer.
        """
        recommendations: list[TransferRecommendation] = []

        try:
            # Search for the target campaign
            target_nodes = await self._ks.search(
                organization_id=organization_id,
                query=f"campaign {target_campaign_id}",
                type_filter="campaign",
                limit=1,
            )
            if not target_nodes:
                return recommendations

            target = target_nodes[0]
            target_name = target.get("name", "Unknown")
            target_props = target.get("properties", {})

            # Find related campaigns
            related = await self._ks.search(
                organization_id=organization_id,
                query=target_name,
                type_filter="campaign",
                limit=limit + 5,
            )

            for node in related:
                node_id = node.get("properties", {}).get("campaign_id", node.get("id", ""))
                if str(node_id) == target_campaign_id:
                    continue

                # Generate transfer recommendations based on similarity
                similarity = node.get("similarity", 0.5)
                if similarity < _TRANSFER_CONFIDENCE_MIN:
                    continue

                source_name = node.get("name", "Unknown")

                # Create pattern-based recommendations
                pattern = CampaignPattern(
                    pattern_id=f"transfer_{node_id}_{target_campaign_id}",
                    pattern_type=PatternType.AUDIENCE_PATTERN,
                    title=f"Transfer audience strategy from '{source_name}'",
                    description=(
                        f"Campaign '{source_name}' shares {similarity:.0%} similarity "
                        f"with '{target_name}'. Consider applying audience targeting "
                        f"strategy from the source."
                    ),
                    campaign_ids=[str(node_id), target_campaign_id],
                    strength=similarity,
                    sample_size=2,
                    confidence=min(similarity * 0.8, 0.9),
                )

                recommendations.append(TransferRecommendation(
                    source_campaign_id=str(node_id),
                    source_campaign_name=source_name,
                    target_campaign_id=target_campaign_id,
                    target_campaign_name=target_name,
                    pattern=pattern,
                    transfer_strategy=(
                        f"Apply audience targeting parameters from '{source_name}' "
                        f"to '{target_name}'. Start with a 20% budget test before "
                        f"full rollout."
                    ),
                    expected_lift=f"Estimated {similarity * 15:.0f}% improvement in reach",
                    confidence=round(pattern.confidence, 2),
                    prerequisites=[
                        "Validate audience overlap analysis",
                        "Set up A/B test with 20% budget allocation",
                        "Define success metrics and monitoring cadence",
                    ],
                ))

        except Exception:
            logger.exception("Transfer suggestion failed")

        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        return recommendations[:limit]

    async def get_learning_insights(
        self,
        organization_id: UUID,
        limit: int = 10,
    ) -> list[LearningInsight]:
        """Get aggregated learning insights from cross-campaign analysis."""
        insights: list[LearningInsight] = []

        # Mine patterns first
        patterns = await self.mine_patterns(organization_id, limit=20)

        # Convert strong patterns into insights
        for pattern in patterns:
            if pattern.strength >= _PATTERN_STRENGTH_THRESHOLD:
                priority = (
                    "high" if pattern.strength >= 0.7
                    else "medium" if pattern.strength >= 0.5
                    else "low"
                )
                insights.append(LearningInsight(
                    insight_id=f"insight_{pattern.pattern_id}",
                    title=f"Pattern: {pattern.title}",
                    description=pattern.description,
                    supporting_campaigns=pattern.campaign_ids,
                    insight_type=pattern.pattern_type.value,
                    priority=priority,
                    recommended_actions=[
                        f"Review {pattern.pattern_type.value} across {len(pattern.campaign_ids)} campaigns",
                        f"Apply winning strategy to underperformers",
                    ],
                ))

        insights.sort(key=lambda i: i.priority == "high", reverse=True)
        return insights[:limit]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_campaigns(
        self,
        organization_id: UUID,
        campaign_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch campaign nodes from the knowledge graph."""
        try:
            raw = await self._ks.search(
                organization_id=organization_id,
                query="campaign performance metrics",
                type_filter="campaign",
                limit=50,
            )
            if campaign_ids:
                id_set = set(campaign_ids)
                raw = [
                    r for r in raw
                    if r.get("id") in id_set
                    or r.get("properties", {}).get("campaign_id") in id_set
                ]
            return raw
        except Exception:
            return []

    async def _mine_pattern_type(
        self,
        organization_id: UUID,
        campaigns: list[dict[str, Any]],
        pattern_type: PatternType,
    ) -> list[CampaignPattern]:
        """Mine patterns of a specific type across campaigns."""
        patterns: list[CampaignPattern] = []

        if pattern_type == PatternType.AUDIENCE_PATTERN:
            patterns = await self._mine_audience_patterns(organization_id, campaigns)
        elif pattern_type == PatternType.CONTENT_PATTERN:
            patterns = await self._mine_content_patterns(organization_id, campaigns)
        elif pattern_type == PatternType.CHANNEL_PATTERN:
            patterns = await self._mine_channel_patterns(organization_id, campaigns)

        return patterns

    async def _mine_audience_patterns(
        self,
        organization_id: UUID,
        campaigns: list[dict[str, Any]],
    ) -> list[CampaignPattern]:
        """Find audience patterns across campaigns."""
        patterns: list[CampaignPattern] = []

        # Group campaigns by similar names/descriptions
        clusters = self._cluster_campaigns(campaigns, key="name")

        for cluster_name, cluster_campaigns in clusters.items():
            if len(cluster_campaigns) >= _MIN_CAMPAIGNS_FOR_PATTERN:
                # Calculate similarity from name overlap
                avg_similarity = self._average_similarity(cluster_campaigns)
                if avg_similarity >= _PATTERN_STRENGTH_THRESHOLD:
                    patterns.append(CampaignPattern(
                        pattern_id=f"audience_{cluster_name[:20]}_{len(patterns)}",
                        pattern_type=PatternType.AUDIENCE_PATTERN,
                        title=f"Shared audience pattern in '{cluster_name}' campaigns",
                        description=(
                            f"{len(cluster_campaigns)} campaigns targeting similar "
                            f"audiences with {avg_similarity:.0%} overlap."
                        ),
                        campaign_ids=[
                            c.get("id", "") for c in cluster_campaigns
                        ],
                        strength=avg_similarity,
                        sample_size=len(cluster_campaigns),
                        confidence=min(0.5 + len(cluster_campaigns) * 0.1, 0.9),
                    ))

        return patterns

    async def _mine_content_patterns(
        self,
        organization_id: UUID,
        campaigns: list[dict[str, Any]],
    ) -> list[CampaignPattern]:
        """Find content patterns across campaigns."""
        patterns: list[CampaignPattern] = []

        # Search for content nodes related to campaigns
        for campaign in campaigns[:5]:
            try:
                content_nodes = await self._ks.search(
                    organization_id=organization_id,
                    query=campaign.get("name", ""),
                    type_filter="content",
                    limit=5,
                )
                if len(content_nodes) >= 2:
                    avg_sim = sum(n.get("similarity", 0) for n in content_nodes) / len(content_nodes)
                    if avg_sim >= _PATTERN_STRENGTH_THRESHOLD:
                        patterns.append(CampaignPattern(
                            pattern_id=f"content_{campaign.get('id', '')[:8]}_{len(patterns)}",
                            pattern_type=PatternType.CONTENT_PATTERN,
                            title=f"Content pattern for '{campaign.get('name', 'Unknown')}'",
                            description=(
                                f"Found {len(content_nodes)} related content pieces with "
                                f"{avg_sim:.0%} similarity for this campaign theme."
                            ),
                            campaign_ids=[campaign.get("id", "")],
                            strength=avg_sim,
                            sample_size=len(content_nodes),
                            confidence=min(0.4 + avg_sim * 0.4, 0.85),
                        ))
            except Exception:
                continue

        return patterns

    async def _mine_channel_patterns(
        self,
        organization_id: UUID,
        campaigns: list[dict[str, Any]],
    ) -> list[CampaignPattern]:
        """Find channel patterns across campaigns."""
        patterns: list[CampaignPattern] = []

        # Search for channel nodes
        try:
            channel_nodes = await self._ks.search(
                organization_id=organization_id,
                query="marketing channels social media email",
                type_filter="channel",
                limit=10,
            )

            if len(channel_nodes) >= 2:
                # Group by channel name similarity
                clusters = self._cluster_campaigns(channel_nodes, key="name")
                for ch_name, ch_nodes in clusters.items():
                    if len(ch_nodes) >= 2:
                        avg_sim = self._average_similarity(ch_nodes)
                        patterns.append(CampaignPattern(
                            pattern_id=f"channel_{ch_name[:20]}_{len(patterns)}",
                            pattern_type=PatternType.CHANNEL_PATTERN,
                            title=f"Channel pattern: {ch_name}",
                            description=(
                                f"{len(ch_nodes)} channels show {avg_sim:.0%} similarity "
                                f"in usage across campaigns."
                            ),
                            campaign_ids=[n.get("id", "") for n in ch_nodes],
                            strength=avg_sim,
                            sample_size=len(ch_nodes),
                            confidence=min(0.4 + avg_sim * 0.3, 0.8),
                        ))
        except Exception:
            pass

        return patterns

    def _cluster_campaigns(
        self,
        campaigns: list[dict[str, Any]],
        key: str = "name",
    ) -> dict[str, list[dict[str, Any]]]:
        """Simple clustering by name prefix similarity."""
        clusters: dict[str, list[dict[str, Any]]] = {}
        for c in campaigns:
            name = c.get(key, "unknown")
            # Use first word as cluster key
            prefix = name.split()[0].lower() if name.split() else "unknown"
            clusters.setdefault(prefix, []).append(c)
        return clusters

    def _average_similarity(self, nodes: list[dict[str, Any]]) -> float:
        """Calculate average similarity from node list."""
        similarities = [n.get("similarity", 0.5) for n in nodes]
        return sum(similarities) / len(similarities) if similarities else 0.0
