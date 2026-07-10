from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class AgentRole(str, Enum):
    CEO = "ceo"
    CAMPAIGN_DIRECTOR = "campaign_director"
    CONTENT_DIRECTOR = "content_director"
    ANALYTICS_DIRECTOR = "analytics_director"
    WORKFLOW_DIRECTOR = "workflow_director"
    SPECIALIST = "specialist"


class AgentStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class Agent:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    role: AgentRole = AgentRole.SPECIALIST
    status: AgentStatus = AgentStatus.IDLE
    parent_id: UUID | None = None
    capabilities: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        name: str,
        role: AgentRole,
        capabilities: list[str] | None = None,
        parent_id: UUID | None = None,
    ) -> "Agent":
        return cls(
            name=name,
            role=role,
            capabilities=capabilities or [],
            parent_id=parent_id,
        )

    def set_status(self, status: AgentStatus) -> None:
        self.status = status
        self.updated_at = now()
