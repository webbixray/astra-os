import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.email.email_event import EmailEvent
from app.infrastructure.db.base import Base


class EmailEventModel(Base):
    __tablename__ = "email_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def to_domain(self) -> EmailEvent:
        return EmailEvent(
            id=self.id,
            campaign_id=self.campaign_id,
            event_type=self.event_type,
            recipient_email=self.recipient_email,
            metadata=dict(self.event_metadata) if self.event_metadata else {},
            occurred_at=self.occurred_at.replace(tzinfo=None),
            created_at=self.created_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, e: EmailEvent) -> "EmailEventModel":
        return cls(
            id=e.id,
            campaign_id=e.campaign_id,
            event_type=e.event_type,
            recipient_email=e.recipient_email,
            event_metadata=e.metadata,
            occurred_at=e.occurred_at,
            created_at=e.created_at,
        )
