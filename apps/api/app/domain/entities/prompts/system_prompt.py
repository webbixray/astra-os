from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


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
        return cls(
            name=name,
            content=content,
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
