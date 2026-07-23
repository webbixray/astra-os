"""Content Schedule Model — SQLAlchemy ORM model for recurring content schedules."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.content.content_schedule import ContentSchedule, ScheduleStatus
from app.infrastructure.db.base import Base


def _utc_now() -> datetime:
    """Return current UTC time with timezone."""
    return datetime.now(UTC)


class ContentScheduleModel(Base):
    """SQLAlchemy model for content_schedules table."""

    __tablename__ = "content_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ScheduleStatus.ACTIVE.value, nullable=False, index=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_runs: Mapped[int | None] = mapped_column(nullable=True)
    schedule_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    def to_domain(self) -> ContentSchedule:
        """Convert ORM model to domain entity."""
        return ContentSchedule(
            id=self.id,
            organization_id=self.organization_id,
            content_id=self.content_id,
            name=self.name,
            platform=self.platform,
            cron_expression=self.cron_expression,
            timezone=self.timezone,
            status=ScheduleStatus(self.status),
            next_run_at=self.next_run_at,
            last_run_at=self.last_run_at,
            run_count=self.run_count,
            max_runs=self.max_runs,
            metadata=dict(self.schedule_metadata) if self.schedule_metadata else {},
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, schedule: ContentSchedule) -> "ContentScheduleModel":
        """Create ORM model from domain entity."""
        return cls(
            id=schedule.id,
            organization_id=schedule.organization_id,
            content_id=schedule.content_id,
            name=schedule.name,
            platform=schedule.platform,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            status=schedule.status.value,
            next_run_at=schedule.next_run_at,
            last_run_at=schedule.last_run_at,
            run_count=schedule.run_count,
            max_runs=schedule.max_runs,
            schedule_metadata=schedule.metadata,
            created_by=schedule.created_by,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
