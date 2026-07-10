import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.reports.report_template import ReportDeliveryLog, ReportTemplate
from app.infrastructure.db.base import Base


class ReportTemplateModel(Base):
    __tablename__ = "report_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> ReportTemplate:
        return ReportTemplate(
            id=self.id, organization_id=self.organization_id,
            name=self.name, description=self.description,
            report_type=self.report_type,
            config=dict(self.config) if self.config else {},
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, t: ReportTemplate) -> "ReportTemplateModel":
        return cls(
            id=t.id, organization_id=t.organization_id,
            name=t.name, description=t.description,
            report_type=t.report_type, config=t.config,
            created_by=t.created_by,
            created_at=t.created_at, updated_at=t.updated_at,
        )


class ReportDeliveryLogModel(Base):
    __tablename__ = "report_delivery_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(20), default="csv", nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="download", nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> ReportDeliveryLog:
        return ReportDeliveryLog(
            id=self.id, organization_id=self.organization_id,
            template_id=self.template_id, schedule_id=self.schedule_id,
            report_type=self.report_type, format=self.format,
            channel=self.channel, recipient=self.recipient,
            status=self.status, error_message=self.error_message,
            file_url=self.file_url,
            generated_at=self.generated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, d: ReportDeliveryLog) -> "ReportDeliveryLogModel":
        return cls(
            id=d.id, organization_id=d.organization_id,
            template_id=d.template_id, schedule_id=d.schedule_id,
            report_type=d.report_type, format=d.format,
            channel=d.channel, recipient=d.recipient,
            status=d.status, error_message=d.error_message,
            file_url=d.file_url, generated_at=d.generated_at,
        )
