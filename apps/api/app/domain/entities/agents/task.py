from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentTask:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: UUID | None = None
    assigned_by: UUID | None = None
    parent_task_id: UUID | None = None
    result: dict | None = field(default_factory=dict)
    error: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        title: str,
        description: str,
        assigned_by: UUID,
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: UUID | None = None,
    ) -> "AgentTask":
        return cls(
            title=title,
            description=description,
            assigned_by=assigned_by,
            priority=priority,
            parent_task_id=parent_task_id,
        )

    def assign(self, agent_id: UUID) -> None:
        self.assigned_to = agent_id
        self.status = TaskStatus.ASSIGNED
        self.updated_at = now()

    def start(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = now()

    def complete(self, result: dict | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        if result:
            self.result = result
        self.updated_at = now()

    def fail(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = now()
