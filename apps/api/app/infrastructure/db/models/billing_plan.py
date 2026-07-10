import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.organization import BillingPlan
from app.infrastructure.db.base import Base


class BillingPlanModel(Base):
    __tablename__ = "org_billing_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    plan_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(50), default="monthly", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> BillingPlan:
        return BillingPlan(
            id=self.id, organization_id=self.organization_id,
            plan_tier=self.plan_tier, billing_cycle=self.billing_cycle,
            subscription_status=self.subscription_status,
            current_period_start=self.current_period_start.replace(tzinfo=None),
            current_period_end=self.current_period_end.replace(tzinfo=None),
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, bp: BillingPlan) -> "BillingPlanModel":
        return cls(
            id=bp.id, organization_id=bp.organization_id,
            plan_tier=bp.plan_tier, billing_cycle=bp.billing_cycle,
            subscription_status=bp.subscription_status,
            current_period_start=bp.current_period_start,
            current_period_end=bp.current_period_end,
            created_at=bp.created_at, updated_at=bp.updated_at,
        )
