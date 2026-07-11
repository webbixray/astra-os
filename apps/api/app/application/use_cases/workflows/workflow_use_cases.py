from uuid import UUID

from app.domain.common import now
from app.domain.entities.workflows.execution import ExecutionStep, WorkflowExecution
from app.domain.entities.workflows.workflow import (
    Workflow,
    WorkflowStatus,
)
from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.domain.services.workflow_runner import WorkflowRunner
from app.infrastructure.db.repositories.workflows.workflow_repository import (
    WorkflowRepository,
)
from app.infrastructure.temporal.client import TemporalWorkflowClient


class CreateWorkflowUseCase:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo

    async def execute(
        self,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        description: str = "",
    ) -> Workflow:
        workflow = Workflow.create(
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            description=description,
        )
        return await self.repo.save(workflow)


class GetWorkflowUseCase:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo

    async def execute(self, workflow_id: UUID) -> Workflow | None:
        return await self.repo.find_by_id(workflow_id)


class ListWorkflowsUseCase:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo

    async def execute(self, organization_id: UUID, status: str | None = None) -> list[Workflow]:
        return await self.repo.find_by_organization(organization_id, status)


class UpdateWorkflowUseCase:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo

    async def execute(
        self,
        workflow_id: UUID,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        nodes: list[dict] | None = None,
        edges: list[dict] | None = None,
    ) -> Workflow | None:
        workflow = await self.repo.find_by_id(workflow_id)
        if not workflow:
            return None
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if status is not None:
            workflow.status = WorkflowStatus(status)
        if nodes is not None:
            from app.domain.entities.workflows.workflow import WorkflowNode

            workflow.nodes = [WorkflowNode(**n) if isinstance(n, dict) else n for n in nodes]
        if edges is not None:
            from app.domain.entities.workflows.workflow import WorkflowEdge

            workflow.edges = [WorkflowEdge(**e) if isinstance(e, dict) else e for e in edges]
        workflow.updated_at = now()
        return await self.repo.save(workflow)


class ExecuteWorkflowUseCase:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo
        self.runner = WorkflowRunner()
        self.temporal = TemporalWorkflowClient()

    async def execute(
        self,
        workflow_id: UUID,
        organization_id: UUID,
        triggered_by: UUID,
    ) -> dict:
        workflow = await self.repo.find_by_id(workflow_id)
        if not workflow:
            raise EntityNotFoundError("Workflow", str(workflow_id))

        execution = WorkflowExecution.create(
            workflow_id=workflow_id,
            organization_id=organization_id,
            triggered_by=triggered_by,
        )
        execution = await self.repo.save_execution(execution)

        temporal_result = await self.temporal.execute_workflow(
            workflow_id=workflow_id,
            organization_id=organization_id,
            name=workflow.name,
            nodes=[n.__dict__ for n in workflow.nodes],
            edges=[e.__dict__ for e in workflow.edges],
        )

        if temporal_result:
            execution.status = temporal_result.get("status", "completed")
            execution.steps = [
                ExecutionStep(**s) if isinstance(s, dict) else s
                for s in temporal_result.get("steps", [])
            ]
            execution = await self.repo.save_execution(execution)
            return {
                "execution_id": str(execution.id),
                "status": execution.status.value
                if hasattr(execution.status, "value")
                else execution.status,
                "steps": [s.__dict__ for s in execution.steps],
                "engine": "temporal",
            }

        execution = await self.runner.execute(workflow, execution)
        execution = await self.repo.save_execution(execution)

        return {
            "execution_id": str(execution.id),
            "status": execution.status.value,
            "steps": [s.__dict__ for s in execution.steps],
            "engine": "sync",
        }
