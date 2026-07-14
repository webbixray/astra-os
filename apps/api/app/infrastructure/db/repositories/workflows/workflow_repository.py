from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.workflows.execution import (
    ExecutionStatus,
    ExecutionStep,
    WorkflowExecution,
)
from app.domain.entities.workflows.version import WorkflowVersion
from app.domain.entities.workflows.workflow import (
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from app.infrastructure.db.models.workflows.workflow_model import (
    WorkflowExecutionModel,
    WorkflowModel,
    WorkflowVersionModel,
)


def _model_to_entity(model: WorkflowModel) -> Workflow:
    nodes = [WorkflowNode(**n) if isinstance(n, dict) else n for n in (model.nodes or [])]
    edges = [WorkflowEdge(**e) if isinstance(e, dict) else e for e in (model.edges or [])]
    return Workflow(
        id=model.id,
        organization_id=model.organization_id,
        name=model.name,
        description=model.description or "",
        status=WorkflowStatus(model.status),
        nodes=nodes,
        edges=edges,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


# --- Version conversion ---

class WorkflowVersion:
    """Workflow version entity."""

    def __init__(
        self,
        id: UUID,
        workflow_id: UUID,
        organization_id: UUID,
        version_number: int,
        name: str,
        description: str,
        nodes: list,
        edges: list,
        change_summary: str,
        created_by: UUID,
        created_at: datetime,
    ):
        self.id = id
        self.workflow_id = workflow_id
        self.organization_id = organization_id
        self.version_number = version_number
        self.name = name
        self.description = description
        self.nodes = nodes
        self.edges = edges
        self.change_summary = change_summary
        self.created_by = created_by
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "organization_id": str(self.organization_id),
            "version_number": self.version_number,
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "edges": self.edges,
            "change_summary": self.change_summary,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


def _version_model_to_entity(model: WorkflowVersionModel) -> WorkflowVersion:
    def _model_to_entity(model: WorkflowModel) -> Workflow:
        nodes = [WorkflowNode(**n) if isinstance(n, dict) else n for n in (model.nodes or [])]
        edges = [WorkflowEdge(**e) if isinstance(e, dict) else e for e in (model.edges or [])]
        return Workflow(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            description=model.description or "",
            status=WorkflowStatus(model.status),
            nodes=nodes,
            edges=edges,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


    def _version_model_to_entity(model: WorkflowVersionModel) -> WorkflowVersion:
        nodes = [WorkflowNode(**n) if isinstance(n, dict) else n for n in (model.nodes or [])]
        edges = [WorkflowEdge(**e) if isinstance(e, dict) else e for e in (model.edges or [])]
        return WorkflowVersion(
            id=model.id,
            workflow_id=model.workflow_id,
            organization_id=model.organization_id,
            version_number=model.version_number,
            name=model.name,
            description=model.description or "",
            nodes=nodes,
            edges=edges,
            change_summary=model.change_summary or "",
            created_by=model.created_by,
            created_at=model.created_at,
        )


    def _entity_to_model(entity: Workflow) -> WorkflowModel:
        return WorkflowModel(
            id=entity.id,
            organization_id=entity.organization_id,
            name=entity.name,
            description=entity.description,
            status=entity.status.value,
            nodes=[n.__dict__ for n in entity.nodes],
            edges=[e.__dict__ for e in entity.edges],
            created_by=entity.created_by,
        )


    def _version_entity_to_model(entity: WorkflowVersion) -> WorkflowVersionModel:
        return WorkflowVersionModel(
            id=entity.id,
            workflow_id=entity.workflow_id,
            organization_id=entity.organization_id,
            version_number=entity.version_number,
            name=entity.name,
            description=entity.description,
            nodes=[n.__dict__ for n in entity.nodes],
            edges=[e.__dict__ for e in entity.edges],
            change_summary=entity.change_summary,
            created_by=entity.created_by,
        )


    def _execution_model_to_entity(model: WorkflowExecutionModel) -> WorkflowExecution:
        steps = [ExecutionStep(**s) if isinstance(s, dict) else s for s in (model.steps or [])]
        return WorkflowExecution(
            id=model.id,
            workflow_id=model.workflow_id,
            organization_id=model.organization_id,
            status=ExecutionStatus(model.status),
            steps=steps,
            triggered_by=model.triggered_by,
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


    def _execution_entity_to_model(entity: WorkflowExecution) -> WorkflowExecutionModel:
        return WorkflowExecutionModel(
            id=entity.id,
            workflow_id=entity.workflow_id,
            organization_id=entity.organization_id,
            status=entity.status.value,
            steps=[s.__dict__ for s in entity.steps],
            triggered_by=entity.triggered_by,
            error=entity.error,
        )


class WorkflowRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, workflow: Workflow) -> Workflow:
        model = _entity_to_model(workflow)
        existing = await self.db.get(WorkflowModel, model.id)
        if existing:
            for attr in ("name", "description", "status", "nodes", "edges", "updated_at"):
                setattr(existing, attr, getattr(model, attr))
            model = existing
        else:
            self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def find_by_id(self, workflow_id: UUID) -> Workflow | None:
        result = await self.db.execute(select(WorkflowModel).where(WorkflowModel.id == workflow_id))
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def find_by_organization(self, org_id: UUID, status: str | None = None) -> list[Workflow]:
        query = select(WorkflowModel).where(WorkflowModel.organization_id == org_id)
        if status:
            query = query.where(WorkflowModel.status == status)
        query = query.order_by(WorkflowModel.created_at.desc())
        result = await self.db.execute(query)
        models = list(result.scalars().all())
        return [_model_to_entity(m) for m in models]

    async def delete(self, workflow_id: UUID) -> None:
        result = await self.db.execute(select(WorkflowModel).where(WorkflowModel.id == workflow_id))
        model = result.scalar_one_or_none()
        if model:
            await self.db.delete(model)
            await self.db.flush()

    async def save_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        model = _execution_entity_to_model(execution)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _execution_model_to_entity(model)

    async def find_executions_by_workflow(self, workflow_id: UUID) -> list[WorkflowExecution]:
        result = await self.db.execute(
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_id == workflow_id)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        models = list(result.scalars().all())
        return [_execution_model_to_entity(m) for m in models]

    async def save_version(self, version: WorkflowVersion) -> WorkflowVersion:
        model = _version_entity_to_model(version)
        existing = await self.db.get(WorkflowVersionModel, model.id)
        if existing:
            for attr in (
                "name",
                "description",
                "nodes",
                "edges",
                "change_summary",
                "created_at",
            ):
                setattr(existing, attr, getattr(model, attr))
            model = existing
        else:
            self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _version_model_to_entity(model)

    async def find_versions_by_workflow(self, workflow_id: UUID) -> list[WorkflowVersion]:
        result = await self.db.execute(
            select(WorkflowVersionModel)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version_number.desc())
        )
        models = list(result.scalars().all())
        return [_version_model_to_entity(m) for m in models]

    async def find_version(self, workflow_id: UUID, version_number: int) -> WorkflowVersion | None:
        result = await self.db.execute(
            select(WorkflowVersionModel).where(
                WorkflowVersionModel.workflow_id == workflow_id,
                WorkflowVersionModel.version_number == version_number,
            )
        )
        model = result.scalar_one_or_none()
        return _version_model_to_entity(model) if model else None

    async def get_current_version(self, workflow_id: UUID) -> WorkflowVersion | None:
        result = await self.db.execute(
            select(WorkflowVersionModel)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version_number.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _version_model_to_entity(model) if model else None

    # --- Version methods ---

    async def create_version(
        self,
        workflow: Workflow,
        version_number: int,
        change_summary: str,
        created_by: UUID,
    ) -> WorkflowVersion:
        """Create a new version snapshot of a workflow."""
        model = WorkflowVersionModel(
            workflow_id=workflow.id,
            organization_id=workflow.organization_id,
            version_number=version_number,
            name=workflow.name,
            description=workflow.description,
            nodes=[n.__dict__ for n in workflow.nodes],
            edges=[e.__dict__ for e in workflow.edges],
            change_summary=change_summary,
            created_by=created_by,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _version_model_to_entity(model)

    async def get_version(self, workflow_id: UUID, version_number: int) -> WorkflowVersion | None:
        result = await self.db.execute(
            select(WorkflowVersionModel).where(
                WorkflowVersionModel.workflow_id == workflow_id,
                WorkflowVersionModel.version_number == version_number,
            )
        )
        model = result.scalar_one_or_none()
        return _version_model_to_entity(model) if model else None

    async def get_latest_version(self, workflow_id: UUID) -> WorkflowVersion | None:
        result = await self.db.execute(
            select(WorkflowVersionModel)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version_number.desc())
        )
        model = result.scalar_one_or_none()
        return _version_model_to_entity(model) if model else None

    async def list_versions(self, workflow_id: UUID) -> list[WorkflowVersion]:
        result = await self.db.execute(
            select(WorkflowVersionModel)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version_number.desc())
        )
        models = list(result.scalars().all())
        return [_version_model_to_entity(m) for m in models]

    async def get_next_version_number(self, workflow_id: UUID) -> int:
        result = await self.db.execute(
            select(WorkflowVersionModel.version_number)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version_number.desc())
        )
        latest = result.scalar_one_or_none()
        return (latest or 0) + 1
