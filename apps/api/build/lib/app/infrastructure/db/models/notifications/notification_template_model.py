import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.notifications.notification import NotificationTemplate
from app.infrastructure.db.base import Base


class NotificationTemplateModel(Base):
    __tablename__ = "notification_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    title_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, default="", nullable=False)
    variables: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> NotificationTemplate:
        return NotificationTemplate(
            id=self.id,
            organization_id=self.organization_id,
            name=self.name,
            type=self.type,
            channel=self.channel,
            title_template=self.title_template,
            body_template=self.body_template,
            variables=list(self.variables or []),
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, t: NotificationTemplate) -> "NotificationTemplateModel":
        return cls(
            id=t.id,
            organization_id=t.organization_id,
            name=t.name,
            type=t.type,
            channel=t.channel,
            title_template=t.title_template,
            body_template=t.body_template,
            variables=t.variables,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
