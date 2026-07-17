import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.reports.report_schedule import ReportSchedule
from app.infrastructure.db.base import Base


class ReportScheduleModel(Base):
    __tablename__ = "report_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    recipients: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> ReportSchedule:
        return ReportSchedule(
            id=self.id,
            organization_id=self.organization_id,
            name=self.name,
            report_type=self.report_type,
            frequency=self.frequency,
            recipients=list(self.recipients) if self.recipients else [],
            config=dict(self.config) if self.config else {},
            next_run_at=self.next_run_at.replace(tzinfo=None) if self.next_run_at else None,
            last_run_at=self.last_run_at.replace(tzinfo=None) if self.last_run_at else None,
            is_active=self.is_active,
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, schedule: ReportSchedule) -> "ReportScheduleModel":
        return cls(
            id=schedule.id,
            organization_id=schedule.organization_id,
            name=schedule.name,
            report_type=schedule.report_type,
            frequency=schedule.frequency,
            recipients=schedule.recipients,
            config=schedule.config,
            next_run_at=schedule.next_run_at,
            last_run_at=schedule.last_run_at,
            is_active=schedule.is_active,
            created_by=schedule.created_by,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
