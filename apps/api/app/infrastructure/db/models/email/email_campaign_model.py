import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.email.email_campaign import EmailCampaign
from app.infrastructure.db.base import Base


class EmailCampaignModel(Base):
    __tablename__ = "email_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bounce_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    campaign_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> EmailCampaign:
        return EmailCampaign(
            id=self.id, organization_id=self.organization_id, provider_id=self.provider_id,
            name=self.name, subject=self.subject, body=self.body, from_email=self.from_email,
            from_name=self.from_name, recipient_count=self.recipient_count,
            sent_count=self.sent_count, open_count=self.open_count, click_count=self.click_count,
            bounce_count=self.bounce_count, status=self.status, scheduled_at=self.scheduled_at.replace(tzinfo=None) if self.scheduled_at else None,
            sent_at=self.sent_at.replace(tzinfo=None) if self.sent_at else None,
            metadata=dict(self.campaign_metadata) if self.campaign_metadata else {}, created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None), updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, c: EmailCampaign) -> "EmailCampaignModel":
        return cls(
            id=c.id, organization_id=c.organization_id, provider_id=c.provider_id,
            name=c.name, subject=c.subject, body=c.body, from_email=c.from_email,
            from_name=c.from_name, recipient_count=c.recipient_count,
            sent_count=c.sent_count, open_count=c.open_count, click_count=c.click_count,
            bounce_count=c.bounce_count, status=c.status, scheduled_at=c.scheduled_at,
            sent_at=c.sent_at, campaign_metadata=c.metadata, created_by=c.created_by,
            created_at=c.created_at, updated_at=c.updated_at,
        )
