from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"
    APPROVAL = "approval"
    END = "end"


NODE_CATEGORIES: dict[NodeType, str] = {
    NodeType.TRIGGER: "When something happens",
    NodeType.ACTION: "Do something",
    NodeType.CONDITION: "Branch based on condition",
    NodeType.DELAY: "Wait for a period",
    NodeType.APPROVAL: "Request human approval",
    NodeType.END: "End the workflow",
}


@dataclass
class WorkflowNode:
    id: str = ""
    type: NodeType = NodeType.ACTION
    label: str = ""
    config: dict = field(default_factory=dict)
    position_x: float = 0
    position_y: float = 0

    @classmethod
    def create(
        cls,
        id: str,
        type: NodeType,
        label: str,
        config: dict | None = None,
        position_x: float = 0,
        position_y: float = 0,
    ) -> "WorkflowNode":
        return cls(
            id=id,
            type=type,
            label=label or type.value,
            config=config or {},
            position_x=position_x,
            position_y=position_y,
        )


@dataclass
class WorkflowEdge:
    id: str = ""
    source_id: str = ""
    target_id: str = ""
    label: str = ""

    @classmethod
    def create(
        cls,
        id: str,
        source_id: str,
        target_id: str,
        label: str = "",
    ) -> "WorkflowEdge":
        return cls(id=id, source_id=source_id, target_id=target_id, label=label)


@dataclass
class Workflow:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        description: str = "",
    ) -> "Workflow":
        if not name or not name.strip():
            raise ValidationError("Workflow name is required")
        return cls(
            organization_id=organization_id,
            name=name.strip(),
            description=description,
            created_by=created_by,
            nodes=[
                WorkflowNode.create(
                    id="trigger-1",
                    type=NodeType.TRIGGER,
                    label="Start",
                    position_x=250,
                    position_y=0,
                ),
                WorkflowNode.create(
                    id="end-1",
                    type=NodeType.END,
                    label="End",
                    position_x=250,
                    position_y=300,
                ),
            ],
            edges=[
                WorkflowEdge.create(
                    id="e-trigger-end",
                    source_id="trigger-1",
                    target_id="end-1",
                ),
            ],
        )

    def add_node(self, node: WorkflowNode) -> None:
        self.nodes.append(node)
        self.updated_at = now()

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if node_id not in (e.source_id, e.target_id)]
        self.updated_at = now()

    def add_edge(self, edge: WorkflowEdge) -> None:
        self.edges.append(edge)
        self.updated_at = now()

    def remove_edge(self, edge_id: str) -> None:
        self.edges = [e for e in self.edges if e.id != edge_id]
        self.updated_at = now()

    def transition_to(self, new_status: WorkflowStatus) -> None:
        allowed = {
            WorkflowStatus.DRAFT: [WorkflowStatus.ACTIVE, WorkflowStatus.ARCHIVED],
            WorkflowStatus.ACTIVE: [WorkflowStatus.PAUSED, WorkflowStatus.COMPLETED, WorkflowStatus.ARCHIVED],
            WorkflowStatus.PAUSED: [WorkflowStatus.ACTIVE, WorkflowStatus.ARCHIVED],
            WorkflowStatus.COMPLETED: [WorkflowStatus.ARCHIVED],
            WorkflowStatus.ARCHIVED: [],
        }
        allowed_statuses = allowed.get(self.status, [])
        if new_status not in allowed_statuses:
            raise ValidationError(
                f"Cannot transition from '{self.status.value}' to '{new_status.value}'"
            )
        self.status = new_status
        self.updated_at = now()
