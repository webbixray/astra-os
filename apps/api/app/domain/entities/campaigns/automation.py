from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

# ── Budget Allocation ────────────────────────────────────────────────────────

ALLOCATION_STRATEGIES = ["equal", "weighted", "performance_based", "ai_optimized"]


@dataclass
class BudgetAllocationRule:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    campaign_id: UUID = field(default_factory=uuid4)
    name: str = ""
    strategy: str = "equal"
    allocations: dict = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, campaign_id: UUID, name: str,
               strategy: str = "equal",
               allocations: dict | None = None) -> "BudgetAllocationRule":
        if not name or not name.strip():
            raise ValidationError("Rule name is required")
        if strategy not in ALLOCATION_STRATEGIES:
            raise ValidationError(f"Invalid strategy: {strategy}")
        return cls(
            organization_id=organization_id, campaign_id=campaign_id,
            name=name.strip(), strategy=strategy,
            allocations=allocations or {},
        )

    def toggle(self, enabled: bool) -> None:
        self.enabled = enabled
        self.updated_at = now()


# ── Bid Optimization ─────────────────────────────────────────────────────────

BID_STRATEGIES = ["target_cpa", "target_roas", "maximize_clicks",
                  "maximize_conversions", "enhanced_cpc"]


@dataclass
class BidOptimizationRule:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    ad_account_id: UUID = field(default_factory=uuid4)
    name: str = ""
    strategy: str = "target_cpa"
    target_value: float = 0.0
    min_bid: float = 0.0
    max_bid: float = 0.0
    enabled: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, ad_account_id: UUID,
               name: str, strategy: str = "target_cpa",
               target_value: float = 0.0, min_bid: float = 0.0,
               max_bid: float = 0.0) -> "BidOptimizationRule":
        if not name or not name.strip():
            raise ValidationError("Rule name is required")
        if strategy not in BID_STRATEGIES:
            raise ValidationError(f"Invalid bid strategy: {strategy}")
        return cls(
            organization_id=organization_id, ad_account_id=ad_account_id,
            name=name.strip(), strategy=strategy,
            target_value=target_value, min_bid=min_bid, max_bid=max_bid,
        )


# ── Audience Segmentation ────────────────────────────────────────────────────

AUDIENCE_SOURCES = ["behavioral", "demographic", "custom", "lookalike", "ai_predicted"]


@dataclass
class AudienceSegment:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    source: str = "custom"
    criteria: dict = field(default_factory=dict)
    predicted_size: int = 0
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, name: str,
               source: str = "custom",
               criteria: dict | None = None) -> "AudienceSegment":
        if not name or not name.strip():
            raise ValidationError("Segment name is required")
        if source not in AUDIENCE_SOURCES:
            raise ValidationError(f"Invalid source: {source}")
        return cls(
            organization_id=organization_id, name=name.strip(),
            source=source, criteria=criteria or {},
        )


# ── Content Recommendations ──────────────────────────────────────────────────

RECOMMENDATION_TYPES = ["topic", "format", "channel", "timing", "headline", "cta"]


@dataclass
class ContentRecommendation:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    campaign_id: UUID | None = None
    recommendation_type: str = "topic"
    title: str = ""
    description: str = ""
    confidence_score: float = 0.0
    metadata: dict = field(default_factory=dict)
    applied: bool = False
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, recommendation_type: str,
               title: str, description: str = "",
               campaign_id: UUID | None = None,
               confidence_score: float = 0.0,
               metadata: dict | None = None) -> "ContentRecommendation":
        if not title or not title.strip():
            raise ValidationError("Recommendation title is required")
        if recommendation_type not in RECOMMENDATION_TYPES:
            raise ValidationError(f"Invalid type: {recommendation_type}")
        return cls(
            organization_id=organization_id, campaign_id=campaign_id,
            recommendation_type=recommendation_type,
            title=title.strip(), description=description,
            confidence_score=confidence_score, metadata=metadata or {},
        )

    def mark_applied(self) -> None:
        self.applied = True


# ── Automation Rules Engine ──────────────────────────────────────────────────

TRIGGER_TYPES = ["schedule", "metric_threshold", "budget_exhausted",
                 "performance_drop", "anomaly_detected", "campaign_status_change"]

ACTION_TYPES = ["adjust_budget", "adjust_bid", "pause_campaign",
                "activate_campaign", "change_channel_allocation",
                "send_notification", "create_content"]


@dataclass
class AutomationRule:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    trigger_type: str = "schedule"
    trigger_config: dict = field(default_factory=dict)
    action_type: str = "send_notification"
    action_config: dict = field(default_factory=dict)
    enabled: bool = True
    last_evaluated_at: datetime | None = None
    last_triggered_at: datetime | None = None
    execution_count: int = 0
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, name: str, trigger_type: str,
               action_type: str, trigger_config: dict | None = None,
               action_config: dict | None = None,
               description: str = "",
               created_by: UUID | None = None) -> "AutomationRule":
        if not name or not name.strip():
            raise ValidationError("Rule name is required")
        if trigger_type not in TRIGGER_TYPES:
            raise ValidationError(f"Invalid trigger type: {trigger_type}")
        if action_type not in ACTION_TYPES:
            raise ValidationError(f"Invalid action type: {action_type}")
        return cls(
            organization_id=organization_id, name=name.strip(),
            description=description, trigger_type=trigger_type,
            trigger_config=trigger_config or {},
            action_type=action_type, action_config=action_config or {},
            created_by=created_by or uuid4(),
        )

    def toggle(self, enabled: bool) -> None:
        self.enabled = enabled
        self.updated_at = now()

    def record_execution(self) -> None:
        self.execution_count += 1
        self.last_triggered_at = now()
        self.updated_at = now()
