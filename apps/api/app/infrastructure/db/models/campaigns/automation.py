import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.campaigns.automation import (
    AudienceSegment,
    AutomationRule,
    BidOptimizationRule,
    BudgetAllocationRule,
    ContentRecommendation,
)
from app.infrastructure.db.base import Base


class BudgetAllocationRuleModel(Base):
    __tablename__ = "budget_allocation_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    allocations: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> BudgetAllocationRule:
        return BudgetAllocationRule(
            id=self.id, organization_id=self.organization_id,
            campaign_id=self.campaign_id, name=self.name,
            strategy=self.strategy,
            allocations=dict(self.allocations) if self.allocations else {},
            enabled=self.enabled,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, r: BudgetAllocationRule) -> "BudgetAllocationRuleModel":
        return cls(
            id=r.id, organization_id=r.organization_id,
            campaign_id=r.campaign_id, name=r.name,
            strategy=r.strategy, allocations=r.allocations,
            enabled=r.enabled,
            created_at=r.created_at, updated_at=r.updated_at,
        )


class BidOptimizationRuleModel(Base):
    __tablename__ = "bid_optimization_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    ad_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_bid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_bid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> BidOptimizationRule:
        return BidOptimizationRule(
            id=self.id, organization_id=self.organization_id,
            ad_account_id=self.ad_account_id, name=self.name,
            strategy=self.strategy, target_value=self.target_value,
            min_bid=self.min_bid, max_bid=self.max_bid,
            enabled=self.enabled,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, r: BidOptimizationRule) -> "BidOptimizationRuleModel":
        return cls(
            id=r.id, organization_id=r.organization_id,
            ad_account_id=r.ad_account_id, name=r.name,
            strategy=r.strategy, target_value=r.target_value,
            min_bid=r.min_bid, max_bid=r.max_bid,
            enabled=r.enabled,
            created_at=r.created_at, updated_at=r.updated_at,
        )


class AudienceSegmentModel(Base):
    __tablename__ = "audience_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    predicted_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> AudienceSegment:
        return AudienceSegment(
            id=self.id, organization_id=self.organization_id,
            name=self.name, source=self.source,
            criteria=dict(self.criteria) if self.criteria else {},
            predicted_size=self.predicted_size,
            confidence_score=self.confidence_score,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, s: AudienceSegment) -> "AudienceSegmentModel":
        return cls(
            id=s.id, organization_id=s.organization_id,
            name=s.name, source=s.source, criteria=s.criteria,
            predicted_size=s.predicted_size,
            confidence_score=s.confidence_score,
            created_at=s.created_at, updated_at=s.updated_at,
        )


class ContentRecommendationModel(Base):
    __tablename__ = "content_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommendation_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> ContentRecommendation:
        return ContentRecommendation(
            id=self.id, organization_id=self.organization_id,
            campaign_id=self.campaign_id,
            recommendation_type=self.recommendation_type,
            title=self.title, description=self.description,
            confidence_score=self.confidence_score,
            metadata=dict(self.recommendation_metadata) if self.recommendation_metadata else {},
            applied=self.applied,
            created_at=self.created_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, r: ContentRecommendation) -> "ContentRecommendationModel":
        return cls(
            id=r.id, organization_id=r.organization_id,
            campaign_id=r.campaign_id,
            recommendation_type=r.recommendation_type,
            title=r.title, description=r.description,
            confidence_score=r.confidence_score,
            recommendation_metadata=r.metadata, applied=r.applied,
            created_at=r.created_at,
        )


class AutomationRuleModel(Base):
    __tablename__ = "automation_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> AutomationRule:
        return AutomationRule(
            id=self.id, organization_id=self.organization_id,
            name=self.name, description=self.description,
            trigger_type=self.trigger_type,
            trigger_config=dict(self.trigger_config) if self.trigger_config else {},
            action_type=self.action_type,
            action_config=dict(self.action_config) if self.action_config else {},
            enabled=self.enabled,
            last_evaluated_at=self.last_evaluated_at.replace(tzinfo=None) if self.last_evaluated_at else None,
            last_triggered_at=self.last_triggered_at.replace(tzinfo=None) if self.last_triggered_at else None,
            execution_count=self.execution_count,
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, r: AutomationRule) -> "AutomationRuleModel":
        return cls(
            id=r.id, organization_id=r.organization_id,
            name=r.name, description=r.description,
            trigger_type=r.trigger_type,
            trigger_config=r.trigger_config,
            action_type=r.action_type, action_config=r.action_config,
            enabled=r.enabled,
            last_evaluated_at=r.last_evaluated_at,
            last_triggered_at=r.last_triggered_at,
            execution_count=r.execution_count,
            created_by=r.created_by,
            created_at=r.created_at, updated_at=r.updated_at,
        )
