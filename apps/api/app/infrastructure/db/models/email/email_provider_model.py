import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.email.email_provider import EmailProvider
from app.infrastructure.db.base import Base
from app.infrastructure.db.types import EncryptedString


class EmailProviderModel(Base):
    __tablename__ = "email_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(EncryptedString(2048), nullable=False)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> EmailProvider:
        return EmailProvider(
            id=self.id, organization_id=self.organization_id, provider_type=self.provider_type,
            name=self.name, api_key=self.api_key, from_email=self.from_email,
            from_name=self.from_name, is_verified=self.is_verified, is_active=self.is_active,
            config=dict(self.config) if self.config else {}, created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None), updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, p: EmailProvider) -> "EmailProviderModel":
        return cls(
            id=p.id, organization_id=p.organization_id, provider_type=p.provider_type,
            name=p.name, api_key=p.api_key, from_email=p.from_email, from_name=p.from_name,
            is_verified=p.is_verified, is_active=p.is_active, config=p.config,
            created_by=p.created_by, created_at=p.created_at, updated_at=p.updated_at,
        )
