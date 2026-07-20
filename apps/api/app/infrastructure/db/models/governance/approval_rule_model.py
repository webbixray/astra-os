"""Approval Rule DB model."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.governance.approval import ApprovalRule, RuleTrigger
from app.infrastructure.db.base import Base


class ApprovalRuleModel(Base):
    __tablename__ = "approval_rules"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    conditions: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    approver_roles: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    approver_users: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    escalation_users: Mapped[list] = mapped_column(JSON, nullable=True, default=list)

    approval_timeout_hours: Mapped[int] = mapped_column(Integer, default=24)
    auto_reject_on_timeout: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[str] = mapped_column(String(30), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(30), nullable=False)

    def to_domain(self) -> ApprovalRule:
        return ApprovalRule(
            id=self.id if isinstance(self.id, str) else str(self.id),
            organization_id=self.organization_id
            if isinstance(self.organization_id, str)
            else str(self.organization_id),
            name=self.name,
            description=self.description or "",
            trigger=RuleTrigger(self.trigger),
            is_active=self.is_active,
            priority=self.priority,
            conditions=self.conditions or {},
            approver_roles=self.approver_roles or ["admin"],
            approver_users=self.approver_users or [],
            escalation_users=self.escalation_users or [],
            approval_timeout_hours=self.approval_timeout_hours,
            auto_reject_on_timeout=self.auto_reject_on_timeout,
        )

    @classmethod
    def from_domain(cls, rule: ApprovalRule) -> ApprovalRuleModel:
        return cls(
            id=str(rule.id),
            organization_id=str(rule.organization_id),
            name=rule.name,
            description=rule.description,
            trigger=rule.trigger.value,
            is_active=rule.is_active,
            priority=rule.priority,
            conditions=rule.conditions,
            approver_roles=rule.approver_roles,
            approver_users=[str(u) for u in rule.approver_users],
            escalation_users=[str(u) for u in rule.escalation_users],
            approval_timeout_hours=rule.approval_timeout_hours,
            auto_reject_on_timeout=rule.auto_reject_on_timeout,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
        )
