"""Agent Action DB model."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.governance.autonomy import AgentAction, AutonomyLevel
from app.infrastructure.db.base import Base


class AgentActionModel(Base):
    __tablename__ = "agent_actions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    details: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    reasoning: Mapped[str] = mapped_column(String(5000), nullable=True, default="")
    reasoning_trace: Mapped[list] = mapped_column(JSON, nullable=True, default=list)

    autonomy_level: Mapped[int] = mapped_column(Integer, default=0)
    was_auto_executed: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_request_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    result: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    model_used: Mapped[str] = mapped_column(String(100), nullable=True, default="")

    created_at: Mapped[str] = mapped_column(String(30), nullable=False)

    def to_domain(self) -> AgentAction:
        return AgentAction(
            id=self.id if isinstance(self.id, str) else str(self.id),
            organization_id=self.organization_id if isinstance(self.organization_id, str) else str(self.organization_id),
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=self.action,
            resource_type=self.resource_type or "",
            resource_id=self.resource_id or "",
            details=self.details or {},
            reasoning=self.reasoning or "",
            reasoning_trace=self.reasoning_trace or [],
            autonomy_level=AutonomyLevel(self.autonomy_level),
            was_auto_executed=self.was_auto_executed,
            approval_request_id=self.approval_request_id,
            success=self.success,
            error_message=self.error_message or "",
            result=self.result or {},
            tokens_used=self.tokens_used,
            cost_usd=self.cost_usd,
            model_used=self.model_used or "",
        )

    @classmethod
    def from_domain(cls, action: AgentAction) -> AgentActionModel:
        return cls(
            id=str(action.id),
            organization_id=str(action.organization_id),
            agent_id=action.agent_id,
            agent_type=action.agent_type,
            action=action.action,
            resource_type=action.resource_type,
            resource_id=action.resource_id,
            details=action.details,
            reasoning=action.reasoning,
            reasoning_trace=action.reasoning_trace,
            autonomy_level=action.autonomy_level.value,
            was_auto_executed=action.was_auto_executed,
            approval_request_id=str(action.approval_request_id) if action.approval_request_id else None,
            success=action.success,
            error_message=action.error_message,
            result=action.result,
            tokens_used=action.tokens_used,
            cost_usd=action.cost_usd,
            model_used=action.model_used,
            created_at=action.created_at.isoformat(),
        )
