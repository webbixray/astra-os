"""Workflow Version Entity — Immutable version snapshots of workflows.

M5 Workflow Engine: Provides version history for workflows, enabling
replay debugging and rollback capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.workflows.workflow import (
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)


@dataclass
class WorkflowVersion:
    """An immutable version snapshot of a workflow."""

    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    version_number: int = 1
    name: str = ""
    description: str = ""
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    change_summary: str = ""
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now())
    is_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "organization_id": str(self.organization_id),
            "version_number": self.version_number,
            "name": self.name,
            "description": self.description,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "change_summary": self.change_summary,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "is_current": self.is_current,
        }

    def to_workflow(self, created_by: UUID | None = None) -> Workflow:
        """Restore this version as a workflow entity."""
        return Workflow(
            id=self.workflow_id,
            organization_id=self.organization_id,
            name=self.name,
            description=self.description,
            status=WorkflowStatus.DRAFT,
            nodes=list(self.nodes),
            edges=list(self.edges),
            created_by=created_by or self.created_by,
        )

    @classmethod
    def from_workflow(
        cls,
        workflow: Workflow,
        version_number: int,
        created_by: UUID,
        change_summary: str = "",
    ) -> "WorkflowVersion":
        """Create a version snapshot from a workflow."""
        return cls(
            workflow_id=workflow.id,
            organization_id=workflow.organization_id,
            version_number=version_number,
            name=workflow.name,
            description=workflow.description,
            nodes=list(workflow.nodes),
            edges=list(workflow.edges),
            change_summary=change_summary,
            created_by=created_by,
        )