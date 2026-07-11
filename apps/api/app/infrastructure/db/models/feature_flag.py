import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.organization import FeatureFlag
from app.infrastructure.db.base import Base


class FeatureFlagModel(Base):
    __tablename__ = "org_feature_flags"
    __table_args__ = (Index("idx_org_feature_flags_org_key", "organization_id", "feature_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> FeatureFlag:
        return FeatureFlag(
            id=self.id,
            organization_id=self.organization_id,
            feature_key=self.feature_key,
            enabled=self.enabled,
            config=dict(self.config) if self.config else {},
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, ff: FeatureFlag) -> "FeatureFlagModel":
        return cls(
            id=ff.id,
            organization_id=ff.organization_id,
            feature_key=ff.feature_key,
            enabled=ff.enabled,
            config=ff.config,
            created_at=ff.created_at,
            updated_at=ff.updated_at,
        )
