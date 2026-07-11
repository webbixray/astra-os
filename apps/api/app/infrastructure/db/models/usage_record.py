import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.organization import UsageRecord
from app.infrastructure.db.base import Base


class UsageRecordModel(Base):
    __tablename__ = "org_usage_records"
    __table_args__ = (
        Index(
            "idx_org_usage_records_org_metric_recorded", "organization_id", "metric", "recorded_at"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def to_domain(self) -> UsageRecord:
        return UsageRecord(
            id=self.id,
            organization_id=self.organization_id,
            metric=self.metric,
            value=self.value,
            recorded_at=self.recorded_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, u: UsageRecord) -> "UsageRecordModel":
        return cls(
            id=u.id,
            organization_id=u.organization_id,
            metric=u.metric,
            value=u.value,
            recorded_at=u.recorded_at,
        )
