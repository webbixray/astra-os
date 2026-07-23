import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.content.content_publish import ContentPublish
from app.infrastructure.db.base import Base


class ContentPublishModel(Base):
    __tablename__ = "content_publishes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> ContentPublish:
        return ContentPublish(
            id=self.id,
            content_id=self.content_id,
            platform=self.platform,
            status=self.status,
            scheduled_at=self.scheduled_at.replace(tzinfo=None) if self.scheduled_at else None,
            published_at=self.published_at.replace(tzinfo=None) if self.published_at else None,
            external_url=self.external_url,
            error_message=self.error_message,
            metadata=dict(self.publish_metadata) if self.publish_metadata else {},
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, publish: ContentPublish) -> "ContentPublishModel":
        return cls(
            id=publish.id,
            content_id=publish.content_id,
            platform=publish.platform,
            status=publish.status,
            scheduled_at=publish.scheduled_at,
            published_at=publish.published_at,
            external_url=publish.external_url,
            error_message=publish.error_message,
            publish_metadata=publish.metadata,
            created_at=publish.created_at,
            updated_at=publish.updated_at,
        )
