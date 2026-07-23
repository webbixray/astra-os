"""Workflow Versioning — Version history and replay debugging for workflows.

M5 Workflow Engine: Provides workflow version management, allowing users to
save, list, restore, and replay workflow versions for debugging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.entities.workflows.workflow import (
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from app.domain.events.event_bus import DomainEvent, DomainEventType
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class WorkflowVersion:
    """A versioned snapshot of a workflow."""

    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    version_number: int = 1
    name: str = ""
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    change_summary: str = ""
    is_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "version_number": self.version_number,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "change_summary": self.change_summary,
            "is_current": self.is_current,
        }

    @classmethod
    def from_workflow(
        cls,
        workflow: Workflow,
        version_number: int,
        created_by: UUID,
        change_summary: str = "",
    ) -> WorkflowVersion:
        """Create a version snapshot from a workflow."""
        return cls(
            workflow_id=workflow.id,
            version_number=version_number,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status,
            nodes=list(workflow.nodes),
            edges=list(workflow.edges),
            created_by=created_by,
            change_summary=change_summary,
        )

    def restore_to_workflow(self, created_by: UUID | None = None) -> Workflow:
        """Restore this version as a new workflow (or update existing)."""
        return Workflow(
            id=self.workflow_id,
            organization_id=self.nodes[0].__dict__.get("organization_id", uuid4())
            if self.nodes
            else uuid4(),
            name=self.name,
            description=self.description,
            status=WorkflowStatus.DRAFT,
            nodes=list(self.nodes),
            edges=list(self.edges),
            created_by=created_by or self.created_by,
            created_at=now(),
            updated_at=now(),
        )


class WorkflowVersionService:
    """Service for managing workflow versions."""

    def __init__(self, repo) -> None:
        self.repo = repo

    async def create_version(
        self,
        workflow: Workflow,
        created_by: UUID,
        change_summary: str = "",
    ) -> WorkflowVersion:
        """Create a new version for a workflow."""
        # Get current version count
        versions = await self.repo.find_versions_by_workflow(workflow.id)
        version_number = len(versions) + 1

        # Create version
        version = WorkflowVersion.from_workflow(
            workflow=workflow,
            version_number=version_number,
            created_by=created_by,
            change_summary=change_summary,
        )

        # Save version
        await self.repo.save_version(version)

        # Mark all previous versions as not current
        for v in versions:
            v.is_current = False
            await self.repo.save_version(v)

        # Mark this as current
        version.is_current = True
        await self.repo.save_version(version)

        return version

    async def list_versions(self, workflow_id: UUID, limit: int = 50) -> list[WorkflowVersion]:
        """List all versions for a workflow."""
        versions = await self.repo.find_versions_by_workflow(workflow_id)
        # Sort by version number descending (newest first)
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions[:limit]

    async def get_version(self, workflow_id: UUID, version_number: int) -> WorkflowVersion | None:
        """Get a specific version by number."""
        versions = await self.repo.find_versions_by_workflow(workflow_id)
        for v in versions:
            if v.version_number == version_number:
                return v
        return None

    async def get_current_version(self, workflow_id: UUID) -> WorkflowVersion | None:
        """Get the current version."""
        versions = await self.repo.find_versions_by_workflow(workflow_id)
        for v in versions:
            if v.is_current:
                return v
        return None

    async def restore_version(
        self,
        workflow_id: UUID,
        version_number: int,
        restored_by: UUID,
        change_summary: str = "",
    ) -> Workflow:
        """Restore a workflow to a specific version."""
        version = await self.get_version(workflow_id, version_number)
        if not version:
            raise EntityNotFoundError("WorkflowVersion", f"v{version_number}")

        # Create new version from the restored state
        restored_workflow = version.restore_to_workflow(created_by=restored_by)
        restored_workflow.updated_at = now()

        # Save the restored workflow
        saved_workflow = await self.repo.save(restored_workflow)

        # Create a new version entry for the restore
        await self.create_version(
            workflow=saved_workflow,
            created_by=restored_by,
            change_summary=change_summary or f"Restored from version {version_number}",
        )

        return saved_workflow

    async def compare_versions(
        self, workflow_id: UUID, version_a: int, version_b: int
    ) -> dict[str, Any]:
        """Compare two versions and return differences."""
        v_a = await self.get_version(workflow_id, version_a)
        v_b = await self.get_version(workflow_id, version_b)

        if not v_a or not v_b:
            raise EntityNotFoundError("WorkflowVersion", "one or both versions not found")

        return {
            "version_a": v_a.to_dict(),
            "version_b": v_b.to_dict(),
            "nodes_added": self._diff_nodes(v_a.nodes, v_b.nodes, "added"),
            "nodes_removed": self._diff_nodes(v_a.nodes, v_b.nodes, "removed"),
            "nodes_modified": self._diff_nodes(v_a.nodes, v_b.nodes, "modified"),
            "edges_added": self._diff_edges(v_a.edges, v_b.edges, "added"),
            "edges_removed": self._diff_edges(v_a.edges, v_b.edges, "removed"),
            "status_changed": v_a.status != v_b.status,
        }

    def _diff_nodes(
        self, old_nodes: list[WorkflowNode], new_nodes: list[WorkflowNode], diff_type: str
    ) -> list[dict[str, Any]]:
        """Calculate node differences."""
        old_by_id = {n.id: n for n in old_nodes}
        new_by_id = {n.id: n for n in new_nodes}

        result = []
        if diff_type == "added":
            for nid, node in new_by_id.items():
                if nid not in old_by_id:
                    result.append(node.__dict__)
        elif diff_type == "removed":
            for nid, node in old_by_id.items():
                if nid not in new_by_id:
                    result.append(node.__dict__)
        elif diff_type == "modified":
            for nid, old_node in old_by_id.items():
                new_node = new_by_id.get(nid)
                if new_node and old_node != new_node:
                    result.append(
                        {
                            "id": nid,
                            "old": old_node.__dict__,
                            "new": new_node.__dict__,
                        }
                    )
        return result

    def _diff_edges(
        self, old_edges: list[WorkflowEdge], new_edges: list[WorkflowEdge], diff_type: str
    ) -> list[dict[str, Any]]:
        """Calculate edge differences."""
        old_by_id = {e.id: e for e in old_edges}
        new_by_id = {e.id: e for e in new_edges}

        result = []
        if diff_type == "added":
            for eid, edge in new_by_id.items():
                if eid not in old_by_id:
                    result.append(edge.__dict__)
        elif diff_type == "removed":
            for eid, edge in old_by_id.items():
                if eid not in new_by_id:
                    result.append(edge.__dict__)
        return result


@dataclass
class ExecutionReplayStep:
    """A single step in an execution replay."""

    step_number: int
    node_id: str
    node_type: str
    node_label: str
    status: str
    input_data: dict[str, Any]
    output_data: dict[str, Any] | None
    error: str | None
    started_at: str | None
    completed_at: str | None
    duration_ms: int | None


@dataclass
class ExecutionReplay:
    """Complete execution replay data for debugging."""

    execution_id: UUID
    workflow_id: UUID
    workflow_name: str
    workflow_version: int
    status: str
    started_at: str
    completed_at: str | None
    total_duration_ms: int | None
    steps: list[ExecutionReplayStep]
    error: str | None
    context: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "workflow_id": str(self.workflow_id),
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "steps": [s.__dict__ for s in self.steps],
            "error": self.error,
            "context": self.context,
        }


class WorkflowReplayService:
    """Service for replaying and debugging workflow executions."""

    def __init__(self, execution_repo, version_service: WorkflowVersionService) -> None:
        self.execution_repo = execution_repo
        self.version_service = version_service

    async def get_replay(self, execution_id: UUID) -> ExecutionReplay | None:
        """Get full replay data for an execution."""
        execution = await self.execution_repo.find_by_id(execution_id)
        if not execution:
            return None

        # Get workflow version at time of execution
        # (This would ideally be stored on the execution, but we'll infer from context)
        workflow_version = execution.metadata.get("workflow_version", 1)
        if isinstance(workflow_version, str):
            workflow_version = int(workflow_version)

        steps = []
        for i, step in enumerate(execution.steps):
            started = step.started_at
            completed = step.completed_at
            duration = None
            if started and completed:
                duration = int((completed - started).total_seconds() * 1000)

            steps.append(
                ExecutionReplayStep(
                    step_number=i + 1,
                    node_id=step.node_id,
                    node_type=step.node_type if hasattr(step, "node_type") else "unknown",
                    node_label=step.label if hasattr(step, "label") else step.node_id,
                    status=step.status.value if hasattr(step.status, "value") else step.status,
                    input_data=step.input_data if hasattr(step, "input_data") else {},
                    output_data=step.result if hasattr(step, "result") else None,
                    error=step.error if hasattr(step, "error") else None,
                    started_at=started.isoformat() if started else None,
                    completed_at=completed.isoformat() if completed else None,
                    duration_ms=duration,
                )
            )

        started_at = execution.created_at
        completed_at = execution.updated_at if execution.status in ("completed", "failed") else None
        total_duration = None
        if started_at and completed_at:
            total_duration = int((completed_at - started_at).total_seconds() * 1000)

        return ExecutionReplay(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            workflow_name=execution.workflow_name if hasattr(execution, "workflow_name") else "",
            workflow_version=workflow_version,
            status=execution.status.value
            if hasattr(execution.status, "value")
            else execution.status,
            started_at=started_at.isoformat() if started_at else "",
            completed_at=completed_at.isoformat() if completed_at else None,
            total_duration_ms=total_duration,
            steps=steps,
            error=execution.error,
            context=execution.metadata if hasattr(execution, "metadata") else {},
        )

    async def replay_execution(
        self,
        execution_id: UUID,
        runner,
        context: dict[str, Any] | None = None,
    ) -> ExecutionReplay:
        """Replay an execution with the same inputs for debugging."""
        execution = await self.execution_repo.find_by_id(execution_id)
        if not execution:
            raise EntityNotFoundError("WorkflowExecution", str(execution_id))

        workflow = await self.execution_repo.find_workflow_by_id(execution.workflow_id)
        if not workflow:
            raise EntityNotFoundError("Workflow", str(execution.workflow_id))

        # Get the workflow version that was executed
        workflow_version = execution.metadata.get("workflow_version", 1)
        if isinstance(workflow_version, str):
            workflow_version = int(workflow_version)

        # Get that specific version
        version = await self.version_service.get_version(workflow.id, workflow_version)
        if version:
            workflow = version.restore_to_workflow()

        # Re-run with same context
        replay_context = {**(execution.metadata.get("context", {})), **(context or {})}

        new_execution = await runner.execute(
            workflow, execution.organization_id, execution.triggered_by
        )
        new_execution.metadata = {
            **new_execution.metadata,
            "replay_of": str(execution_id),
            "replay_context": replay_context,
        }
        new_execution = await self.execution_repo.save_execution(new_execution)

        return await self.get_replay(new_execution.id)

    async def step_through_execution(self, execution_id: UUID) -> list[ExecutionReplayStep]:
        """Get steps for step-through debugging."""
        replay = await self.get_replay(execution_id)
        if not replay:
            return []
        return replay.steps


# ---------------------------------------------------------------------------
# Domain Events for Versioning
# ---------------------------------------------------------------------------


class WorkflowVersionCreatedEvent(DomainEvent):
    """Event emitted when a new workflow version is created."""

    def __init__(
        self,
        workflow_id: UUID,
        version_number: int,
        created_by: UUID,
        change_summary: str,
        **kwargs,
    ):
        super().__init__(
            event_type=DomainEventType.WORKFLOW_VERSION_CREATED,
            aggregate_id=str(workflow_id),
            aggregate_type="workflow",
            data={
                "workflow_id": str(workflow_id),
                "version_number": version_number,
                "created_by": str(created_by),
                "change_summary": change_summary,
            },
            **kwargs,
        )


class WorkflowVersionRestoredEvent(DomainEvent):
    """Event emitted when a workflow is restored from a version."""

    def __init__(
        self,
        workflow_id: UUID,
        restored_version: int,
        restored_by: UUID,
        **kwargs,
    ):
        super().__init__(
            event_type=DomainEventType.WORKFLOW_VERSION_RESTORED,
            aggregate_id=str(workflow_id),
            aggregate_type="workflow",
            data={
                "workflow_id": str(workflow_id),
                "restored_version": restored_version,
                "restored_by": str(restored_by),
            },
            **kwargs,
        )


class WorkflowExecutionReplayedEvent(DomainEvent):
    """Event emitted when an execution is replayed."""

    def __init__(
        self,
        original_execution_id: UUID,
        new_execution_id: UUID,
        workflow_id: UUID,
        **kwargs,
    ):
        super().__init__(
            event_type=DomainEventType.WORKFLOW_EXECUTION_REPLAYED,
            aggregate_id=str(original_execution_id),
            aggregate_type="workflow_execution",
            data={
                "original_execution_id": str(original_execution_id),
                "new_execution_id": str(new_execution_id),
                "workflow_id": str(workflow_id),
            },
            **kwargs,
        )
