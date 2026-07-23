"""Shadow Mode Entities — E6.2 Beta Launch.

Agents run alongside humans in "shadow mode" to compare decisions,
measure lift, and build confidence before autonomous operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now


class ShadowModeStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    PAUSED = "paused"
    ARCHIVED = "archived"


class DecisionType(str, Enum):
    CAMPAIGN_LAUNCH = "campaign_launch"
    BUDGET_ADJUSTMENT = "budget_adjustment"
    BID_OPTIMIZATION = "bid_optimization"
    TARGETING_CHANGE = "targeting_change"
    CREATIVE_SELECTION = "creative_selection"
    AUDIENCE_EXPANSION = "audience_expansion"
    CONTENT_GENERATION = "content_generation"
    CONTENT_APPROVAL = "content_approval"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"


class ComparisonResult(str, Enum):
    AGREED = "agreed"  # Agent and human made same decision
    AGENT_BETTER = "agent_better"  # Agent's decision outperformed human
    HUMAN_BETTER = "human_better"  # Human's decision outperformed agent
    DIFFERENT = "different"  # Different decisions, outcome TBD
    CONFLICT = "conflict"  # Direct conflict, needs review


class ShadowEventType(str, Enum):
    DECISION_MADE = "decision_made"
    DECISION_COMPARED = "decision_compared"
    OUTCOME_RECORDED = "outcome_recorded"
    LIFT_MEASURED = "lift_measured"
    THRESHOLD_BREACHED = "threshold_breached"
    HUMAN_OVERRIDE = "human_override"
    AGENT_CORRECTED = "agent_corrected"


@dataclass
class ShadowDecision:
    """A decision made by either agent or human in shadow mode."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    shadow_session_id: UUID = field(default_factory=uuid4)

    # Decision context
    decision_type: DecisionType = DecisionType.CAMPAIGN_LAUNCH
    context: dict[str, Any] = field(default_factory=dict)  # Input data for decision
    entity_id: str = ""  # Campaign ID, content ID, etc.
    entity_type: str = ""  # campaign, content, ad_set, etc.

    # Agent's decision
    agent_decision: dict[str, Any] = field(default_factory=dict)
    agent_confidence: float = 0.0
    agent_reasoning: str = ""
    agent_model: str = ""

    # Human's decision (if available)
    human_decision: dict[str, Any] | None = None
    human_confidence: float | None = None
    human_reasoning: str = ""
    decided_by: UUID | None = None

    # Comparison
    comparison_result: ComparisonResult | None = None
    comparison_notes: str = ""
    compared_at: datetime | None = None
    compared_by: UUID | None = None

    # Outcome tracking
    outcome: dict[str, Any] | None = None  # Actual results (ROAS, CTR, etc.)
    outcome_recorded_at: datetime | None = None
    lift_vs_baseline: float | None = None  # Percentage lift vs control

    # Metadata
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "shadow_session_id": str(self.shadow_session_id),
            "decision_type": self.decision_type.value,
            "context": self.context,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "agent_decision": self.agent_decision,
            "agent_confidence": self.agent_confidence,
            "agent_reasoning": self.agent_reasoning,
            "agent_model": self.agent_model,
            "human_decision": self.human_decision,
            "human_confidence": self.human_confidence,
            "human_reasoning": self.human_reasoning,
            "decided_by": str(self.decided_by) if self.decided_by else None,
            "comparison_result": self.comparison_result.value if self.comparison_result else None,
            "comparison_notes": self.comparison_notes,
            "compared_at": self.compared_at.isoformat() if self.compared_at else None,
            "outcome": self.outcome,
            "outcome_recorded_at": self.outcome_recorded_at.isoformat()
            if self.outcome_recorded_at
            else None,
            "lift_vs_baseline": self.lift_vs_baseline,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def has_human_decision(self) -> bool:
        return self.human_decision is not None

    def can_compare(self) -> bool:
        return self.has_human_decision() and self.agent_confidence > 0


@dataclass
class ShadowSession:
    """A shadow mode session for a specific agent/team."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Configuration
    name: str = ""
    description: str = ""
    status: ShadowModeStatus = ShadowModeStatus.ENABLED

    # Agent config
    agent_type: str = ""  # e.g., "CampaignOptimizer", "ContentGenerator"
    agent_config: dict[str, Any] = field(default_factory=dict)
    agent_model: str = ""

    # Scope
    campaigns: list[UUID] = field(default_factory=list)
    ad_accounts: list[str] = field(default_factory=list)
    decision_types: list[DecisionType] = field(default_factory=list)

    # Human reviewers
    reviewers: list[UUID] = field(default_factory=list)
    require_human_approval: bool = True
    auto_approve_threshold: float = 0.9  # Auto-approve if agent confidence > this

    # Comparison settings
    min_decisions_for_comparison: int = 10
    comparison_window_days: int = 7

    # Thresholds for alerts
    agreement_threshold: float = 0.7  # Alert if agreement drops below
    lift_threshold: float = 0.05  # Alert if lift drops below 5%
    max_human_override_rate: float = 0.3  # Alert if override rate > 30%

    # Schedule
    started_at: datetime | None = None
    ended_at: datetime | None = None
    schedule_cron: str | None = None  # e.g., "0 9 * * 1-5" for weekdays 9am

    # Stats
    total_decisions: int = 0
    agent_decisions: int = 0
    human_decisions: int = 0
    agreements: int = 0
    disagreements: int = 0
    human_overrides: int = 0
    agent_corrections: int = 0

    # Lift metrics
    avg_lift_vs_baseline: float = 0.0
    total_lift_measured: int = 0

    # Metadata
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "agent_type": self.agent_type,
            "agent_model": self.agent_model,
            "campaigns": [str(c) for c in self.campaigns],
            "ad_accounts": self.ad_accounts,
            "decision_types": [d.value for d in self.decision_types],
            "reviewers": [str(r) for r in self.reviewers],
            "require_human_approval": self.require_human_approval,
            "auto_approve_threshold": self.auto_approve_threshold,
            "agreement_threshold": self.agreement_threshold,
            "lift_threshold": self.lift_threshold,
            "max_human_override_rate": self.max_human_override_rate,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "schedule_cron": self.schedule_cron,
            "total_decisions": self.total_decisions,
            "agent_decisions": self.agent_decisions,
            "human_decisions": self.human_decisions,
            "agreements": self.agreements,
            "disagreements": self.disagreements,
            "human_overrides": self.human_overrides,
            "agent_corrections": self.agent_corrections,
            "avg_lift_vs_baseline": self.avg_lift_vs_baseline,
            "total_lift_measured": self.total_lift_measured,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def agreement_rate(self) -> float:
        if self.total_decisions == 0:
            return 0.0
        return self.agreements / self.total_decisions

    def human_override_rate(self) -> float:
        if self.agent_decisions == 0:
            return 0.0
        return self.human_overrides / self.agent_decisions

    def is_healthy(self) -> bool:
        """Check if shadow session is within healthy thresholds."""
        if self.total_decisions < self.min_decisions_for_comparison:
            return True  # Not enough data yet
        return (
            self.agreement_rate() >= self.agreement_threshold
            and self.human_override_rate() <= self.max_human_override_rate
        )


@dataclass
class ShadowEvent:
    """Event log for shadow mode activities."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    shadow_session_id: UUID = field(default_factory=uuid4)
    shadow_decision_id: UUID | None = None

    event_type: ShadowEventType = ShadowEventType.DECISION_MADE
    description: str = ""

    # Event data
    data: dict[str, Any] = field(default_factory=dict)

    # Actor
    actor_type: str = "system"  # system, agent, human
    actor_id: UUID | None = None

    # Metadata
    severity: str = "info"  # info, warning, critical
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "shadow_session_id": str(self.shadow_session_id),
            "shadow_decision_id": str(self.shadow_decision_id) if self.shadow_decision_id else None,
            "event_type": self.event_type.value,
            "description": self.description,
            "data": self.data,
            "actor_type": self.actor_type,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "severity": self.severity,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class LiftMeasurement:
    """Measurement of lift between agent and human/baseline decisions."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    shadow_session_id: UUID = field(default_factory=uuid4)

    # Measurement period
    period_start: datetime = field(default_factory=now)
    period_end: datetime = field(default_factory=now)

    # Metrics
    metric_name: str = ""  # e.g., "roas", "ctr", "cpa", "conversion_rate"
    baseline_value: float = 0.0  # Human/control group performance
    agent_value: float = 0.0  # Agent performance
    lift_percentage: float = 0.0  # (agent - baseline) / baseline * 100

    def __post_init__(self) -> None:
        if self.baseline_value != 0:
            self.lift_percentage = (
                (self.agent_value - self.baseline_value) / self.baseline_value
            ) * 100
        else:
            self.lift_percentage = 0.0

    # Statistical significance
    sample_size: int = 0
    p_value: float | None = None
    confidence_interval: tuple[float, float] | None = None
    is_significant: bool = False

    # Context
    decision_types: list[DecisionType] = field(default_factory=list)
    campaigns: list[UUID] = field(default_factory=list)

    # Metadata
    calculated_at: datetime = field(default_factory=now)
    calculated_by: UUID | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "shadow_session_id": str(self.shadow_session_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "agent_value": self.agent_value,
            "lift_percentage": self.lift_percentage,
            "sample_size": self.sample_size,
            "p_value": self.p_value,
            "confidence_interval": list(self.confidence_interval)
            if self.confidence_interval
            else None,
            "is_significant": self.is_significant,
            "decision_types": [d.value for d in self.decision_types],
            "campaigns": [str(c) for c in self.campaigns],
            "calculated_at": self.calculated_at.isoformat(),
            "calculated_by": str(self.calculated_by) if self.calculated_by else None,
            "notes": self.notes,
        }
