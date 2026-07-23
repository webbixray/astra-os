from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class ExecutionStep:
    id: str = ""
    node_id: str = ""
    status: StepStatus = StepStatus.PENDING
    result: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowExecution:
    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    status: ExecutionStatus = ExecutionStatus.PENDING
    steps: list[ExecutionStep] = field(default_factory=list)
    triggered_by: UUID = field(default_factory=uuid4)
    error: str | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        workflow_id: UUID,
        organization_id: UUID,
        triggered_by: UUID,
    ) -> "WorkflowExecution":
        return cls(
            workflow_id=workflow_id,
            organization_id=organization_id,
            triggered_by=triggered_by,
        )

    def start(self) -> None:
        self.status = ExecutionStatus.RUNNING
        self.updated_at = now()

    def complete(self) -> None:
        self.status = ExecutionStatus.COMPLETED
        self.updated_at = now()

    def fail(self, error: str) -> None:
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.updated_at = now()
