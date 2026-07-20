"""Autonomy Config DB model."""

from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.governance.autonomy import AutonomyConfig, AutonomyLevel
from app.infrastructure.db.base import Base


class AutonomyConfigModel(Base):
    __tablename__ = "autonomy_configs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), unique=True, index=True)

    default_level: Mapped[int] = mapped_column(Integer, default=0)
    agent_levels: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    action_overrides: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    auto_approve_spend_limit: Mapped[float] = mapped_column(Float, default=100.0)
    auto_approve_currency: Mapped[str] = mapped_column(String(10), default="USD")
    auto_execute_channels: Mapped[list] = mapped_column(JSON, nullable=True, default=list)

    created_at: Mapped[str] = mapped_column(String(30), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(30), nullable=False)

    def to_domain(self) -> AutonomyConfig:
        agent_levels = {}
        if self.agent_levels:
            for k, v in self.agent_levels.items():
                agent_levels[k] = AutonomyLevel(v)

        action_overrides = {}
        if self.action_overrides:
            for k, v in self.action_overrides.items():
                action_overrides[k] = AutonomyLevel(v)

        return AutonomyConfig(
            id=self.id if isinstance(self.id, str) else str(self.id),
            organization_id=self.organization_id
            if isinstance(self.organization_id, str)
            else str(self.organization_id),
            default_level=AutonomyLevel(self.default_level),
            agent_levels=agent_levels,
            action_overrides=action_overrides,
            auto_approve_spend_limit=self.auto_approve_spend_limit,
            auto_approve_currency=self.auto_approve_currency,
            auto_execute_channels=self.auto_execute_channels or [],
        )

    @classmethod
    def from_domain(cls, config: AutonomyConfig) -> AutonomyConfigModel:
        agent_levels = {k: v.value for k, v in config.agent_levels.items()}
        action_overrides = {k: v.value for k, v in config.action_overrides.items()}

        return cls(
            id=str(config.id),
            organization_id=str(config.organization_id),
            default_level=config.default_level.value,
            agent_levels=agent_levels,
            action_overrides=action_overrides,
            auto_approve_spend_limit=config.auto_approve_spend_limit,
            auto_approve_currency=config.auto_approve_currency,
            auto_execute_channels=config.auto_execute_channels,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )
