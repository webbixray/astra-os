import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt
from app.infrastructure.db.base import Base


class SystemPromptModel(Base):
    __tablename__ = "system_prompts"
    __table_args__ = (
        Index("idx_system_prompts_name_org", "name", "org_id", unique=True),
        Index("idx_system_prompts_category_status", "category", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    def to_domain(self) -> SystemPrompt:
        return SystemPrompt(
            id=self.id,
            org_id=self.org_id,
            name=self.name,
            description=self.description,
            category=PromptCategory(self.category),
            content=self.content,
            variables=list(self.variables) if self.variables else [],
            version=self.version,
            status=PromptStatus(self.status),
            is_builtin=self.is_builtin,
            created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, prompt: SystemPrompt) -> "SystemPromptModel":
        return cls(
            id=prompt.id,
            org_id=prompt.org_id,
            name=prompt.name,
            description=prompt.description,
            category=prompt.category.value,
            content=prompt.content,
            variables=prompt.variables,
            version=prompt.version,
            status=prompt.status.value,
            is_builtin=prompt.is_builtin,
            created_by=prompt.created_by,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )
