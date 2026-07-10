from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    PREFERENCE = "preference"
    FACT = "fact"
    CONTEXT = "context"
    INSIGHT = "insight"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Memory:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    type: MemoryType = MemoryType.CONVERSATION
    importance: MemoryImportance = MemoryImportance.MEDIUM
    key: str = ""
    value: str = ""
    embedding: list[float] | None = None
    metadata: dict = field(default_factory=dict)
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        user_id: UUID,
        key: str,
        value: str,
        type: MemoryType = MemoryType.CONVERSATION,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
    ) -> "Memory":
        return cls(
            organization_id=organization_id,
            user_id=user_id,
            key=key,
            value=value,
            type=type,
            importance=importance,
        )


@dataclass
class ContextMemory:
    current_page: str = ""
    active_campaign_id: str | None = None
    active_content_id: str | None = None
    recent_queries: list[str] = field(default_factory=list)
    user_preferences: dict = field(default_factory=dict)
    session_started_at: datetime = field(default_factory=now)
