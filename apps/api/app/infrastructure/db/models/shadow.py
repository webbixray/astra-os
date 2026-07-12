"""Shadow Mode Repository Implementation — E6.2 Beta Launch."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.shadow_mode import (
    ComparisonResult,
    DecisionType,
    LiftMeasurement,
    ShadowDecision,
    ShadowEvent,
    ShadowEventType,
    ShadowModeStatus,
    ShadowSession,
)
from app.infrastructure.db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func


class ShadowSessionModel(Base):
    __tablename__ = "shadow_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default=ShadowModeStatus.ENABLED.value, index=True)
    agent_type = Column(String(100), nullable=False)
    agent_model = Column(String(100), nullable=False)
    agent_config = Column(String(50), default="{}")
    campaigns = Column(String(50), default="[]")
    ad_accounts = Column(String(50), default="[]")
    decision_types = Column(String(50), default="[]")
    reviewers = Column(String(50), default="[]")
    require_human_approval = Column(String(5), default="true")
    auto_approve_threshold = Column(String(20), default="0.9")
    agreement_threshold = Column(String(20), default="0.7")
    lift_threshold = Column(String(20), default="0.05")
    max_human_override_rate = Column(String(20), default="0.3")
    schedule_cron = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    total_decisions = Column(String(20), default="0")
    agent_decisions = Column(String(20), default="0")
    human_decisions = Column(String(20), default="0")
    agreements = Column(String(20), default="0")
    disagreements = Column(String(20), default="0")
    human_overrides = Column(String(20), default="0")
    agent_corrections = Column(String(20), default="0")

    avg_lift_vs_baseline = Column(String(20), default="0.0")
    total_lift_measured = Column(String(20), default="0")

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ShadowDecisionModel(Base):
    __tablename__ = "shadow_decisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shadow_session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("shadow_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_type = Column(String(50), nullable=False)
    context = Column(String(50), default="{}")
    entity_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    agent_decision = Column(String(50), default="{}")
    agent_confidence = Column(String(20), default="0.0")
    agent_reasoning = Column(Text, default="")
    agent_model = Column(String(100), default="")
    human_decision = Column(String(50), nullable=True)
    human_confidence = Column(String(20), nullable=True)
    human_reasoning = Column(Text, default="")
    decided_by = Column(PG_UUID(as_uuid=True), nullable=True)
    comparison_result = Column(String(50), nullable=True)
    comparison_notes = Column(Text, default="")
    compared_at = Column(DateTime(timezone=True), nullable=True)
    compared_by = Column(PG_UUID(as_uuid=True), nullable=True)
    outcome = Column(String(50), nullable=True)
    outcome_recorded_at = Column(DateTime(timezone=True), nullable=True)
    lift_vs_baseline = Column(String(20), nullable=True)
    tags = Column(String(50), default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ShadowEventModel(Base):
    __tablename__ = "shadow_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shadow_session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("shadow_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shadow_decision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("shadow_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(String(50), nullable=False)
    description = Column(Text, default="")
    data = Column(String(50), default="{}")
    actor_type = Column(String(20), default="system")
    actor_id = Column(PG_UUID(as_uuid=True), nullable=True)
    severity = Column(String(20), default="info")
    tags = Column(String(50), default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiftMeasurementModel(Base):
    __tablename__ = "lift_measurements"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shadow_session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("shadow_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metric_name = Column(String(100), nullable=False)
    baseline_value = Column(String(20), default="0.0")
    agent_value = Column(String(20), default="0.0")
    lift_percentage = Column(String(20), default="0.0")
    sample_size = Column(String(20), default="0")
    p_value = Column(String(20), nullable=True)
    confidence_interval = Column(String(50), nullable=True)
    is_significant = Column(String(5), default="false")
    decision_types = Column(String(50), default="[]")
    campaigns = Column(String(50), default="[]")
    calculated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())