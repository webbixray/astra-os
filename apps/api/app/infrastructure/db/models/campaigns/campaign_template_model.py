import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.campaigns.campaign_template import CampaignTemplate
from app.infrastructure.db.base import Base


class CampaignTemplateModel(Base):
    __tablename__ = "campaign_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    channels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    objective: Mapped[str | None] = mapped_column(String(100), nullable=True)
    budget_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    default_duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> CampaignTemplate:
        return CampaignTemplate(
            id=self.id,
            organization_id=self.organization_id,
            name=self.name,
            description=self.description,
            channels=list(self.channels) if self.channels else [],
            objective=self.objective,
            budget_amount=self.budget_amount,
            budget_currency=self.budget_currency,
            default_duration_days=self.default_duration_days,
            config=dict(self.config) if self.config else {},
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, template: CampaignTemplate) -> "CampaignTemplateModel":
        return cls(
            id=template.id,
            organization_id=template.organization_id,
            name=template.name,
            description=template.description,
            channels=template.channels,
            objective=template.objective,
            budget_amount=template.budget_amount,
            budget_currency=template.budget_currency,
            default_duration_days=template.default_duration_days,
            config=template.config,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
