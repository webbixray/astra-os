"""Design Partner Domain Entities.

M6 Beta Launch: Entities for design partner management, onboarding,
feedback collection, and support ticketing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now


# --- Enums ---

class DesignPartnerTier(str, Enum):
    DESIGN_PARTNER = "design_partner"
    ENTERPRISE = "enterprise"
    STRATEGIC = "strategic"


class DesignPartnerStatus(str, Enum):
    PENDING = "pending"           # Applied, awaiting approval
    APPROVED = "approved"         # Approved, ready for onboarding
    ONBOARDING = "onboarding"     # Active onboarding process
    ACTIVE = "active"             # Fully onboarded, using platform
    PAUSED = "paused"             # Temporarily paused
    CHURNED = "churned"           # Left the program


class FeedbackType(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    DOCUMENTATION = "documentation"
    NPS_SURVEY = "nps_survey"
    GENERAL = "general"


class FeedbackPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


class SupportTicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


# --- Entities ---

@dataclass
class DesignPartner:
    """A design partner organization in the beta program."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    tier: DesignPartnerTier = DesignPartnerTier.DESIGN_PARTNER
    status: DesignPartnerStatus = DesignPartnerStatus.PENDING

    # Assignment
    dedicated_csm_id: UUID | None = None

    # Contract
    contract_signed_at: datetime | None = None
    contract_expires_at: datetime | None = None
    custom_terms: dict[str, Any] = field(default_factory=dict)

    # Billing
    billing_contact_email: str | None = None
    custom_pricing: dict[str, Any] = field(default_factory=dict)

    # Onboarding
    onboarding_started_at: datetime | None = None
    onboarding_completed_at: datetime | None = None
    onboarding_milestones: list[str] = field(default_factory=list)
    onboarding_csm_id: UUID | None = None

    # Engagement metrics
    weekly_active_users: int = 0
    campaigns_run: int = 0
    ai_interactions: int = 0
    last_engagement_at: datetime | None = None

    # NPS
    nps_score: int | None = None
    nps_reason: str | None = None
    nps_responded_at: datetime | None = None

    # Feedback tracking
    feedback_count: int = 0
    feedback_by_type: dict[str, int] = field(default_factory=dict)

    # Support
    support_tier: str = "standard"  # standard, priority, dedicated
    open_tickets: int = 0
    avg_resolution_hours: float = 0.0

    # Notes
    notes: str = ""
    internal_tags: list[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
    approved_at: datetime | None = None
    activated_at: datetime | None = None

    def start_onboarding(self, csm_id: UUID) -> None:
        """Start the onboarding process."""
        self.status = DesignPartnerStatus.ONBOARDING
        self.onboarding_started_at = now()
        self.onboarding_csm_id = csm_id
        self.updated_at = now()

    def complete_onboarding(self) -> None:
        """Complete onboarding and activate partner."""
        self.status = DesignPartnerStatus.ACTIVE
        self.onboarding_completed_at = now()
        self.activated_at = now()
        self.updated_at = now()

    def add_milestone(self, milestone: str) -> None:
        """Add an onboarding milestone."""
        self.onboarding_milestones.append(f"{now().isoformat()}: {milestone}")
        self.updated_at = now()

    def record_feedback(self, feedback_type: FeedbackType) -> None:
        """Record a feedback submission."""
        self.feedback_count += 1
        type_key = feedback_type.value
        self.feedback_by_type[type_key] = self.feedback_by_type.get(type_key, 0) + 1
        self.updated_at = now()

    def update_nps(self, score: int) -> None:
        """Update NPS score."""
        self.nps_score = score
        self.nps_responded_at = now()
        self.updated_at = now()

    def update_engagement(
        self,
        wau: int = 0,
        campaigns: int = 0,
        ai_interactions: int = 0,
    ) -> None:
        """Update engagement metrics."""
        if wau > 0:
            self.weekly_active_users = wau
        if campaigns > 0:
            self.campaigns_run = campaigns
        if ai_interactions > 0:
            self.ai_interactions = ai_interactions
        self.last_engagement_at = now()
        self.updated_at = now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "tier": self.tier.value,
            "status": self.status.value,
            "dedicated_csm_id": str(self.dedicated_csm_id) if self.dedicated_csm_id else None,
            "contract_signed_at": self.contract_signed_at.isoformat() if self.contract_signed_at else None,
            "contract_expires_at": self.contract_expires_at.isoformat() if self.contract_expires_at else None,
            "onboarding_started_at": self.onboarding_started_at.isoformat() if self.onboarding_started_at else None,
            "onboarding_completed_at": self.onboarding_completed_at.isoformat() if self.onboarding_completed_at else None,
            "onboarding_milestones": self.onboarding_milestones,
            "weekly_active_users": self.weekly_active_users,
            "campaigns_run": self.campaigns_run,
            "ai_interactions": self.ai_interactions,
            "last_engagement_at": self.last_engagement_at.isoformat() if self.last_engagement_at else None,
            "nps_score": self.nps_score,
            "feedback_count": self.feedback_count,
            "support_tier": self.support_tier,
            "open_tickets": self.open_tickets,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DesignPartnerFeedback:
    """Feedback submitted by a design partner."""

    id: UUID = field(default_factory=uuid4)
    design_partner_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    type: FeedbackType = FeedbackType.GENERAL
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    status: FeedbackStatus = FeedbackStatus.OPEN

    title: str = ""
    description: str = ""
    feature_area: str | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None

    # NPS
    nps_score: int | None = None
    nps_reason: str | None = None

    # Triage
    assigned_to: UUID | None = None
    triaged_at: datetime | None = None
    resolution_notes: str = ""
    resolved_at: datetime | None = None

    # Tags
    tags: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def triage(self, assignee: UUID) -> None:
        self.status = FeedbackStatus.TRIAGED
        self.assigned_to = assignee
        self.triaged_at = now()
        self.updated_at = now()

    def start_work(self) -> None:
        self.status = FeedbackStatus.IN_PROGRESS
        self.updated_at = now()

    def resolve(self, notes: str = "") -> None:
        self.status = FeedbackStatus.RESOLVED
        self.resolution_notes = notes
        self.resolved_at = now()
        self.updated_at = now()

    def close(self) -> None:
        self.status = FeedbackStatus.CLOSED
        self.updated_at = now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "design_partner_id": str(self.design_partner_id),
            "organization_id": str(self.organization_id),
            "user_id": str(self.user_id),
            "type": self.type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "feature_area": self.feature_area,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "nps_score": self.nps_score,
            "nps_reason": self.nps_reason,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class SupportTicket:
    """Support ticket for a design partner."""

    id: UUID = field(default_factory=uuid4)
    design_partner_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    subject: str = ""
    description: str = ""
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    status: SupportTicketStatus = SupportTicketStatus.OPEN
    channel: str = "email"  # email, slack, in_app, phone
    sla_tier: str = "standard"  # standard, priority, dedicated

    assigned_csm_id: UUID | None = None
    assigned_at: datetime | None = None

    first_responded_at: datetime | None = None
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None

    resolved_at: datetime | None = None
    resolution_summary: str = ""
    customer_satisfaction: int | None = None  # 1-5

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def is_sla_breached(self) -> bool:
        """Check if SLA is breached."""
        if self.status in (SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED):
            return False
        if self.resolution_due_at and now() > self.resolution_due_at:
            return True
        return False

    def hours_to_first_response(self) -> float | None:
        if self.first_responded_at:
            return (self.first_responded_at - self.created_at).total_seconds() / 3600
        if self.first_response_due_at and now() > self.first_response_due_at:
            return (now() - self.created_at).total_seconds() / 3600
        return None

    def hours_to_resolution(self) -> float | None:
        if self.resolved_at:
            return (self.resolved_at - self.created_at).total_seconds() / 3600
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "design_partner_id": str(self.design_partner_id),
            "organization_id": str(self.organization_id),
            "user_id": str(self.user_id),
            "subject": self.subject,
            "priority": self.priority.value,
            "status": self.status.value,
            "channel": self.channel,
            "sla_tier": self.sla_tier,
            "assigned_csm_id": str(self.assigned_csm_id) if self.assigned_csm_id else None,
            "first_responded_at": self.first_responded_at.isoformat() if self.first_responded_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_summary": self.resolution_summary,
            "customer_satisfaction": self.customer_satisfaction,
            "sla_breached": self.is_sla_breached(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }