import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.campaigns.campaign import Campaign
from app.infrastructure.db.base import Base


class CampaignModel(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    budget_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    channels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    objective: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    campaign_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> Campaign:
        return Campaign(
            id=self.id,
            organization_id=self.organization_id,
            name=self.name,
            description=self.description,
            status=self.status,
            budget_amount=self.budget_amount,
            budget_currency=self.budget_currency,
            start_date=self.start_date,
            end_date=self.end_date,
            channels=list(self.channels) if self.channels else [],
            objective=self.objective,
            created_by=self.created_by,
            ai_generated=self.ai_generated,
            metadata=dict(self.campaign_metadata) if self.campaign_metadata else {},
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, campaign: Campaign) -> "CampaignModel":
        return cls(
            id=campaign.id,
            organization_id=campaign.organization_id,
            name=campaign.name,
            description=campaign.description,
            status=campaign.status,
            budget_amount=campaign.budget_amount,
            budget_currency=campaign.budget_currency,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            channels=campaign.channels,
            objective=campaign.objective,
            created_by=campaign.created_by,
            ai_generated=campaign.ai_generated,
            campaign_metadata=campaign.metadata,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
