"""Approval Engine — configurable rules, human task queue, decisions.

Rules define WHEN approval is required:
- Spend threshold (e.g., >$100 requires approval)
- Brand-sensitive content (keywords, categories)
- New audience targeting (first-time segments)
- Channel-specific rules (e.g., all video ads need approval)

Requests are created when a rule triggers:
- Pending → Approved/Rejected/Expired
- Assignable to specific roles or users
- Escalation after timeout

Decisions record the outcome:
- Approve with optional conditions
- Reject with mandatory reason
- Delegate to another user
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


class RuleTrigger(str, Enum):
    """What triggers the approval rule."""

    SPEND_THRESHOLD = "spend_threshold"
    BRAND_SENSITIVE = "brand_sensitive"
    NEW_AUDIENCE = "new_audience"
    CHANNEL_ALL = "channel_all"
    CHANNEL_SPECIFIC = "channel_specific"
    SCHEDULE_CHANGE = "schedule_change"
    CONTENT_PUBLISH = "content_publish"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    DELEGATED = "delegated"
    CANCELLED = "cancelled"


class DecisionAction(str, Enum):
    """Actions an approver can take."""

    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    REQUEST_CHANGES = "request_changes"


@dataclass
class ApprovalRule:
    """Defines when human approval is required.

    Rules are evaluated before agent actions. If any rule matches,
    the action is held for human approval.
    """

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    trigger: RuleTrigger = RuleTrigger.SPEND_THRESHOLD
    is_active: bool = True
    priority: int = 0  # Higher = evaluated first

    # Rule conditions (flexible JSON)
    conditions: dict[str, Any] = field(default_factory=dict)
    # Examples:
    # SPEND_THRESHOLD: {"min_amount": 100, "currency": "USD"}
    # BRAND_SENSITIVE: {"keywords": ["competitor", "guarantee"], "categories": ["health"]}
    # NEW_AUDIENCE: {"require_approval_for_new": true}
    # CHANNEL_SPECIFIC: {"channels": ["ads", "video"]}

    # Who should approve
    approver_roles: list[str] = field(default_factory=lambda: ["admin"])
    approver_users: list[UUID] = field(default_factory=list)
    escalation_users: list[UUID] = field(default_factory=list)

    # Timeout
    approval_timeout_hours: int = 24
    auto_reject_on_timeout: bool = False

    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create_spend_rule(
        cls,
        organization_id: UUID,
        name: str,
        min_amount: float,
        currency: str = "USD",
        approver_roles: list[str] | None = None,
    ) -> ApprovalRule:
        if min_amount <= 0:
            raise ValidationError("Spend threshold must be positive")
        return cls(
            organization_id=organization_id,
            name=name,
            trigger=RuleTrigger.SPEND_THRESHOLD,
            conditions={"min_amount": min_amount, "currency": currency},
            approver_roles=approver_roles or ["admin"],
        )

    @classmethod
    def create_brand_rule(
        cls,
        organization_id: UUID,
        name: str,
        keywords: list[str],
        categories: list[str] | None = None,
    ) -> ApprovalRule:
        if not keywords:
            raise ValidationError("Brand rule must have at least one keyword")
        return cls(
            organization_id=organization_id,
            name=name,
            trigger=RuleTrigger.BRAND_SENSITIVE,
            conditions={"keywords": keywords, "categories": categories or []},
            approver_roles=["admin", "brand_manager"],
        )

    @classmethod
    def create_audience_rule(
        cls,
        organization_id: UUID,
        name: str,
    ) -> ApprovalRule:
        return cls(
            organization_id=organization_id,
            name=name,
            trigger=RuleTrigger.NEW_AUDIENCE,
            conditions={"require_approval_for_new": True},
            approver_roles=["admin", "marketing_director"],
        )

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate whether this rule matches the given context.

        Returns True if approval is required.
        """
        if not self.is_active:
            return False

        if self.trigger == RuleTrigger.SPEND_THRESHOLD:
            amount = context.get("amount", 0)
            min_amount = self.conditions.get("min_amount", 0)
            return amount >= min_amount

        if self.trigger == RuleTrigger.BRAND_SENSITIVE:
            text = context.get("text", "").lower()
            keywords = self.conditions.get("keywords", [])
            return any(kw.lower() in text for kw in keywords)

        if self.trigger == RuleTrigger.NEW_AUDIENCE:
            is_new = context.get("is_new_audience", False)
            return is_new and self.conditions.get("require_approval_for_new", False)

        if self.trigger == RuleTrigger.CHANNEL_SPECIFIC:
            channel = context.get("channel", "")
            channels = self.conditions.get("channels", [])
            return channel in channels

        if self.trigger == RuleTrigger.CHANNEL_ALL:
            return True  # Always requires approval

        return False


@dataclass
class ApprovalRequest:
    """A pending approval request — the human task queue item."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    rule_id: UUID = field(default_factory=uuid4)
    rule_name: str = ""

    # What needs approval
    action_type: str = ""  # e.g., "campaign.launch", "content.publish", "bid.update"
    action_resource_id: str = ""
    action_resource_type: str = ""  # e.g., "campaign", "content", "ad_creative"
    action_context: dict[str, Any] = field(default_factory=dict)
    action_summary: str = ""  # Human-readable summary

    # Who triggered it
    triggered_by_agent_id: str | None = None
    triggered_by_agent_type: str | None = None
    triggered_by_user_id: UUID | None = None

    # Assignment
    status: ApprovalStatus = ApprovalStatus.PENDING
    assigned_to: UUID | None = None
    assigned_role: str = ""

    # Timing
    timeout_at: datetime | None = None
    decided_at: datetime | None = None

    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        rule: ApprovalRule,
        action_type: str,
        action_resource_id: str,
        action_resource_type: str,
        action_summary: str,
        action_context: dict[str, Any] | None = None,
        triggered_by_agent_id: str | None = None,
        triggered_by_agent_type: str | None = None,
    ) -> ApprovalRequest:
        timeout = now() + timedelta(hours=rule.approval_timeout_hours)
        return cls(
            organization_id=organization_id,
            rule_id=rule.id,
            rule_name=rule.name,
            action_type=action_type,
            action_resource_id=action_resource_id,
            action_resource_type=action_resource_type,
            action_context=action_context or {},
            action_summary=action_summary,
            triggered_by_agent_id=triggered_by_agent_id,
            triggered_by_agent_type=triggered_by_agent_type,
            assigned_role=rule.approver_roles[0] if rule.approver_roles else "",
            timeout_at=timeout,
        )

    @property
    def is_expired(self) -> bool:
        if self.timeout_at is None:
            return False
        return now() > self.timeout_at

    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    def assign_to(self, user_id: UUID) -> None:
        self.assigned_to = user_id
        self.updated_at = now()

    def approve(self, decision: ApprovalDecision) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValidationError(f"Cannot approve request in '{self.status.value}' status")
        self.status = ApprovalStatus.APPROVED
        self.decided_at = now()
        self.updated_at = now()

    def reject(self, decision: ApprovalDecision) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValidationError(f"Cannot reject request in '{self.status.value}' status")
        self.status = ApprovalStatus.REJECTED
        self.decided_at = now()
        self.updated_at = now()

    def expire(self) -> None:
        self.status = ApprovalStatus.EXPIRED
        self.decided_at = now()
        self.updated_at = now()

    def cancel(self) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValidationError(f"Cannot cancel request in '{self.status.value}' status")
        self.status = ApprovalStatus.CANCELLED
        self.updated_at = now()


@dataclass
class ApprovalDecision:
    """Records the outcome of an approval request."""

    id: UUID = field(default_factory=uuid4)
    request_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    action: DecisionAction = DecisionAction.APPROVE
    reason: str = ""
    conditions: dict[str, Any] = field(default_factory=dict)
    # e.g., {"max_spend": 500, "duration_days": 7}

    decided_by: UUID = field(default_factory=uuid4)
    decided_at: datetime = field(default_factory=now)

    @classmethod
    def approve(
        cls,
        request_id: UUID,
        organization_id: UUID,
        decided_by: UUID,
        reason: str = "",
        conditions: dict[str, Any] | None = None,
    ) -> ApprovalDecision:
        return cls(
            request_id=request_id,
            organization_id=organization_id,
            action=DecisionAction.APPROVE,
            reason=reason,
            conditions=conditions or {},
            decided_by=decided_by,
        )

    @classmethod
    def reject(
        cls,
        request_id: UUID,
        organization_id: UUID,
        decided_by: UUID,
        reason: str,
    ) -> ApprovalDecision:
        if not reason:
            raise ValidationError("Rejection reason is required")
        return cls(
            request_id=request_id,
            organization_id=organization_id,
            action=DecisionAction.REJECT,
            reason=reason,
            decided_by=decided_by,
        )
