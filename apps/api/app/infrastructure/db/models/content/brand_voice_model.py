import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.content.brand_voice import BrandVoice
from app.infrastructure.db.base import Base


class BrandVoiceModel(Base):
    __tablename__ = "brand_voices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    vocabulary: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    style_guide: Mapped[str] = mapped_column(Text, default="", nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    def to_domain(self) -> BrandVoice:
        return BrandVoice(
            id=self.id,
            organization_id=self.organization_id,
            name=self.name,
            tone=self.tone,
            vocabulary=list(self.vocabulary) if self.vocabulary else [],
            style_guide=self.style_guide,
            target_audience=self.target_audience,
            is_active=self.is_active,
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, voice: BrandVoice) -> "BrandVoiceModel":
        return cls(
            id=voice.id,
            organization_id=voice.organization_id,
            name=voice.name,
            tone=voice.tone,
            vocabulary=voice.vocabulary,
            style_guide=voice.style_guide,
            target_audience=voice.target_audience,
            is_active=voice.is_active,
            created_by=voice.created_by,
            created_at=voice.created_at,
            updated_at=voice.updated_at,
        )
