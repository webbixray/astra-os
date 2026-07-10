import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.notifications.notification import BroadcastAnnouncement
from app.infrastructure.db.base import Base


class BroadcastAnnouncementModel(Base):
    __tablename__ = "broadcast_announcements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    target_role: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    dismissed_by: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> BroadcastAnnouncement:
        return BroadcastAnnouncement(
            id=self.id, organization_id=self.organization_id,
            title=self.title, body=self.body,
            severity=self.severity, target_role=self.target_role,
            created_by=self.created_by,
            dismissed_by=list(self.dismissed_by or []),
            expires_at=self.expires_at.replace(tzinfo=None) if self.expires_at else None,
            created_at=self.created_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, a: BroadcastAnnouncement) -> "BroadcastAnnouncementModel":
        return cls(
            id=a.id, organization_id=a.organization_id,
            title=a.title, body=a.body,
            severity=a.severity, target_role=a.target_role,
            created_by=a.created_by,
            dismissed_by=a.dismissed_by,
            expires_at=a.expires_at,
            created_at=a.created_at,
        )
