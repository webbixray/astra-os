"""Approval Request DB model."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.governance.approval import ApprovalRequest, ApprovalStatus
from app.infrastructure.db.base import Base


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    rule_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_resource_id: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    action_resource_type: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    action_context: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    action_summary: Mapped[str] = mapped_column(String(1000), nullable=True, default="")

    triggered_by_agent_id: Mapped[str] = mapped_column(String(255), nullable=True)
    triggered_by_agent_type: Mapped[str] = mapped_column(String(100), nullable=True)
    triggered_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    assigned_to: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=True)
    assigned_role: Mapped[str] = mapped_column(String(50), nullable=True, default="")

    timeout_at: Mapped[str] = mapped_column(String(30), nullable=True)
    decided_at: Mapped[str] = mapped_column(String(30), nullable=True)

    created_at: Mapped[str] = mapped_column(String(30), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(30), nullable=False)

    def to_domain(self) -> ApprovalRequest:
        from datetime import datetime
        timeout_at = None
        if self.timeout_at:
            timeout_at = datetime.fromisoformat(self.timeout_at)
        decided_at = None
        if self.decided_at:
            decided_at = datetime.fromisoformat(self.decided_at)

        return ApprovalRequest(
            id=self.id if isinstance(self.id, str) else str(self.id),
            organization_id=self.organization_id if isinstance(self.organization_id, str) else str(self.organization_id),
            rule_id=self.rule_id if isinstance(self.rule_id, str) else str(self.rule_id),
            rule_name=self.rule_name or "",
            action_type=self.action_type,
            action_resource_id=self.action_resource_id or "",
            action_resource_type=self.action_resource_type or "",
            action_context=self.action_context or {},
            action_summary=self.action_summary or "",
            triggered_by_agent_id=self.triggered_by_agent_id,
            triggered_by_agent_type=self.triggered_by_agent_type,
            status=ApprovalStatus(self.status),
            assigned_role=self.assigned_role or "",
            timeout_at=timeout_at,
            decided_at=decided_at,
        )

    @classmethod
    def from_domain(cls, req: ApprovalRequest) -> ApprovalRequestModel:
        return cls(
            id=str(req.id),
            organization_id=str(req.organization_id),
            rule_id=str(req.rule_id),
            rule_name=req.rule_name,
            action_type=req.action_type,
            action_resource_id=req.action_resource_id,
            action_resource_type=req.action_resource_type,
            action_context=req.action_context,
            action_summary=req.action_summary,
            triggered_by_agent_id=req.triggered_by_agent_id,
            triggered_by_agent_type=req.triggered_by_agent_type,
            triggered_by_user_id=str(req.triggered_by_user_id) if req.triggered_by_user_id else None,
            status=req.status.value,
            assigned_to=str(req.assigned_to) if req.assigned_to else None,
            assigned_role=req.assigned_role,
            timeout_at=req.timeout_at.isoformat() if req.timeout_at else None,
            decided_at=req.decided_at.isoformat() if req.decided_at else None,
            created_at=req.created_at.isoformat(),
            updated_at=req.updated_at.isoformat(),
        )
