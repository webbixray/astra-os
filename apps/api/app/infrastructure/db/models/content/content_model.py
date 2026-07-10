import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.content.content import Content
from app.infrastructure.db.base import Base


class ContentModel(Base):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    brand_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> Content:
        return Content(
            id=self.id,
            campaign_id=self.campaign_id,
            organization_id=self.organization_id,
            title=self.title,
            content_type=self.content_type,
            body=self.body,
            status=self.status,
            brand_profile_id=self.brand_profile_id,
            generated_by_ai=self.generated_by_ai,
            version=self.version,
            scheduled_at=self.scheduled_at.replace(tzinfo=None) if self.scheduled_at else None,
            published_at=self.published_at.replace(tzinfo=None) if self.published_at else None,
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, content: Content) -> "ContentModel":
        return cls(
            id=content.id,
            campaign_id=content.campaign_id,
            organization_id=content.organization_id,
            title=content.title,
            content_type=content.content_type,
            body=content.body,
            status=content.status,
            brand_profile_id=content.brand_profile_id,
            generated_by_ai=content.generated_by_ai,
            version=content.version,
            scheduled_at=content.scheduled_at,
            published_at=content.published_at,
            created_by=content.created_by,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )
