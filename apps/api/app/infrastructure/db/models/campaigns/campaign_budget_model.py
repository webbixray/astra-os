import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.campaigns.campaign_budget import CampaignBudget
from app.infrastructure.db.base import Base


class CampaignBudgetModel(Base):
    __tablename__ = "campaign_budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    total_budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    alert_threshold: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> CampaignBudget:
        return CampaignBudget(
            id=self.id,
            campaign_id=self.campaign_id,
            total_budget=self.total_budget,
            spent=self.spent,
            currency=self.currency,
            alert_threshold=self.alert_threshold,
            period_start=self.period_start.replace(tzinfo=None) if self.period_start else None,
            period_end=self.period_end.replace(tzinfo=None) if self.period_end else None,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, budget: CampaignBudget) -> "CampaignBudgetModel":
        return cls(
            id=budget.id,
            campaign_id=budget.campaign_id,
            total_budget=budget.total_budget,
            spent=budget.spent,
            currency=budget.currency,
            alert_threshold=budget.alert_threshold,
            period_start=budget.period_start,
            period_end=budget.period_end,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )
