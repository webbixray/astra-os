from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.workflows.workflow_use_cases import (
    CreateWorkflowUseCase,
    ExecuteWorkflowUseCase,
    GetWorkflowUseCase,
    ListWorkflowsUseCase,
    UpdateWorkflowUseCase,
)
from app.infrastructure.db.repositories.workflows.workflow_repository import (
    WorkflowRepository,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    organization_id: UUID
    name: str
    description: str = ""


class UpdateWorkflowRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    nodes: list[dict] | None = None
    edges: list[dict] | None = None


class WorkflowResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str
    status: str
    nodes: list[dict]
    edges: list[dict]
    created_by: UUID
    created_at: str
    updated_at: str


class ExecuteWorkflowRequest(BaseModel):
    organization_id: UUID
    triggered_by: UUID | None = None


async def get_repo(db: AsyncSession = Depends(get_db)) -> WorkflowRepository:
    return WorkflowRepository(db)


def _format_response(workflow) -> WorkflowResponse:
    return WorkflowResponse(
        id=workflow.id,
        organization_id=workflow.organization_id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.value if hasattr(workflow.status, "value") else workflow.status,
        nodes=[n.__dict__ for n in workflow.nodes],
        edges=[e.__dict__ for e in workflow.edges],
        created_by=workflow.created_by,
        created_at=workflow.created_at.isoformat() if workflow.created_at else "",
        updated_at=workflow.updated_at.isoformat() if workflow.updated_at else "",
    )


@router.post("", response_model=WorkflowResponse, status_code=201, summary="Create a new workflow")
async def create_workflow(
    request: CreateWorkflowRequest,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("workflow_automation", request.organization_id, "free", db)
    use_case = CreateWorkflowUseCase(repo)
    workflow = await use_case.execute(
        organization_id=request.organization_id,
        name=request.name,
        created_by=user_id,
        description=request.description,
    )
    return _format_response(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse, summary="Get workflow by ID")
async def get_workflow(
    workflow_id: UUID,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    use_case = GetWorkflowUseCase(repo)
    workflow = await use_case.execute(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await require_org_role(workflow.organization_id, "viewer", user_id, repo.db)
    await require_feature("workflow_automation", workflow.organization_id, "free", db)
    return _format_response(workflow)


@router.get("", response_model=list[WorkflowResponse], summary="List all workflows")
async def list_workflows(
    organization_id: UUID,
    status: str | None = None,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    await require_feature("workflow_automation", organization_id, "free", db)
    use_case = ListWorkflowsUseCase(repo)
    workflows = await use_case.execute(organization_id, status)
    return [_format_response(w) for w in workflows]


@router.patch("/{workflow_id}", response_model=WorkflowResponse, summary="Update a workflow")
async def update_workflow(
    workflow_id: UUID,
    request: UpdateWorkflowRequest,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    get_use_case = GetWorkflowUseCase(repo)
    existing = await get_use_case.execute(workflow_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await require_org_role(existing.organization_id, "member", user_id, db)
    await require_feature("workflow_automation", existing.organization_id, "free", db)
    use_case = UpdateWorkflowUseCase(repo)
    workflow = await use_case.execute(
        workflow_id=workflow_id,
        name=request.name,
        description=request.description,
        status=request.status,
        nodes=request.nodes,
        edges=request.edges,
    )
    return _format_response(workflow)


@router.post("/{workflow_id}/execute", summary="Execute a workflow")
async def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("workflow_automation", request.organization_id, "free", db)
    use_case = ExecuteWorkflowUseCase(repo)
    return await use_case.execute(
        workflow_id=workflow_id,
        organization_id=request.organization_id,
        triggered_by=user_id,
    )


@router.get("/{workflow_id}/executions", summary="List workflow executions")
async def list_executions(
    workflow_id: UUID,
    repo: WorkflowRepository = Depends(get_repo),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    workflow = await repo.find_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await require_org_role(workflow.organization_id, "viewer", user_id, db)
    await require_feature("workflow_automation", workflow.organization_id, "free", db)
    models = await repo.find_executions_by_workflow(workflow_id)
    return [
        {
            "id": str(m.id),
            "status": m.status,
            "steps": m.steps,
            "error": m.error,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in models
    ]
