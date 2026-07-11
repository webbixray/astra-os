from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


class PromptCategory(str, Enum):
    SYSTEM = "system"
    AGENT = "agent"
    CONTENT = "content"
    TOOL = "tool"


class PromptStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


@dataclass
class SystemPrompt:
    id: UUID = field(default_factory=uuid4)
    org_id: UUID | None = None
    name: str = ""
    description: str = ""
    category: PromptCategory = PromptCategory.SYSTEM
    content: str = ""
    variables: list[str] = field(default_factory=list)
    version: int = 1
    status: PromptStatus = PromptStatus.ACTIVE
    is_builtin: bool = False
    created_by: UUID | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        name: str,
        content: str,
        category: PromptCategory = PromptCategory.SYSTEM,
        description: str = "",
        org_id: UUID | None = None,
        variables: list[str] | None = None,
        *,
        is_builtin: bool = False,
        created_by: UUID | None = None,
    ) -> "SystemPrompt":
        if not name or not name.strip():
            raise ValidationError("Prompt name is required")
        if not content or not content.strip():
            raise ValidationError("Prompt content is required")
        return cls(
            name=name.strip(),
            content=content.strip(),
            category=category,
            description=description,
            org_id=org_id,
            variables=variables or [],
            is_builtin=is_builtin,
            created_by=created_by,
        )

    def publish(self) -> None:
        self.status = PromptStatus.ACTIVE
        self.updated_at = now()

    def archive(self) -> None:
        self.status = PromptStatus.ARCHIVED
        self.updated_at = now()

    def draft(self) -> None:
        self.status = PromptStatus.DRAFT
        self.updated_at = now()

    def bump_version(self) -> None:
        self.version += 1
        self.updated_at = now()
