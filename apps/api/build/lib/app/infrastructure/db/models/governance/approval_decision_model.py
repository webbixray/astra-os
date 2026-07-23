"""Approval Decision DB model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.governance.approval import ApprovalDecision, DecisionAction
from app.infrastructure.db.base import Base


class ApprovalDecisionModel(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    request_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    conditions: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    decided_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    decided_at: Mapped[str] = mapped_column(String(30), nullable=False)

    def to_domain(self) -> ApprovalDecision:
        return ApprovalDecision(
            id=self.id if isinstance(self.id, str) else str(self.id),
            request_id=self.request_id
            if isinstance(self.request_id, str)
            else str(self.request_id),
            organization_id=self.organization_id
            if isinstance(self.organization_id, str)
            else str(self.organization_id),
            action=DecisionAction(self.action),
            reason=self.reason or "",
            conditions=self.conditions or {},
            decided_by=self.decided_by
            if isinstance(self.decided_by, str)
            else str(self.decided_by),
        )

    @classmethod
    def from_domain(cls, dec: ApprovalDecision) -> ApprovalDecisionModel:
        return cls(
            id=str(dec.id),
            request_id=str(dec.request_id),
            organization_id=str(dec.organization_id),
            action=dec.action.value,
            reason=dec.reason,
            conditions=dec.conditions,
            decided_by=str(dec.decided_by),
            decided_at=dec.decided_at.isoformat(),
        )
