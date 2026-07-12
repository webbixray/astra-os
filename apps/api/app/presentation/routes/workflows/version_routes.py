"""Workflow Version Routes — API endpoints for workflow versioning and replay debugging.

M5 Workflow Engine: Provides version history, restore, compare, and replay endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.workflows.workflow_use_cases import (
    GetWorkflowUseCase,
    ListWorkflowsUseCase,
)
from app.domain.services.workflow_versioning import (
    ExecutionReplay,
    WorkflowReplayService,
    WorkflowVersion,
    WorkflowVersionService,
)
from app.infrastructure.db.repositories.workflows.workflow_repository import WorkflowRepository
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateVersionRequest(BaseModel):
    change_summary: str = ""


class RestoreVersionRequest(BaseModel):
    change_summary: str | None = None


class CompareVersionsRequest(BaseModel):
    version_a: int
    version_b: int


class ReplayExecutionRequest(BaseModel):
    context: dict | None = None


class VersionResponse(BaseModel):
    id: str
    workflow_id: str
    organization_id: str
    version_number: int
    name: str
    description: str
    node_count: int
    edge_count: int
    change_summary: str
    created_by: str
    created_at: str
    is_current: bool


class VersionDetailResponse(VersionResponse):
    nodes: list[dict]
    edges: list[dict]


class CompareVersionsResponse(BaseModel):
    version_a: VersionResponse
    version_b: VersionResponse
    nodes_added: list[dict]
    nodes_removed: list[dict]
    nodes_modified: list[dict]
    edges_added: list[dict]
    edges_removed: list[dict]
    status_changed: bool


class ReplayResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    workflow_version: int
    status: str
    started_at: str
    completed_at: str | None
    total_duration_ms: int | None
    steps: list[dict]
    error: str | None
    context: dict


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def _get_repo(db: AsyncSession = Depends(get_db)) -> WorkflowRepository:
    return WorkflowRepository(db)


def _get_version_service(repo: WorkflowRepository = Depends(_get_repo)) -> WorkflowVersionService:
    return WorkflowVersionService(repo)


def _get_replay_service(
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> WorkflowReplayService:
    return WorkflowReplayService(repo, version_service)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/workflows/{workflow_id}/versions",
    response_model=VersionDetailResponse,
    status_code=201,
    summary="Create a new version snapshot",
)
async def create_version(
    workflow_id: UUID,
    request: CreateVersionRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "member", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    workflow = await repo.find_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    version = await version_service.create_version(
        workflow=workflow,
        created_by=user_id,
        change_summary=request.change_summary or f"Manual version {len(await version_service.list_versions(workflow_id)) + 1}",
    )
    return version.to_dict()


def request_organization_id(workflow_id: UUID, repo: WorkflowRepository, db: AsyncSession) -> UUID:
    workflow = await repo.find_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.organization_id


@router.get(
    "/workflows/{workflow_id}/versions",
    response_model=list[VersionResponse],
    summary="List all versions for a workflow",
)
async def list_versions(
    workflow_id: UUID,
    limit: int = 50,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> list[dict]:
    await require_org_role(request_organization_id(workflow_id, repo, db), "viewer", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    versions = await version_service.list_versions(workflow_id)
    return [v.to_dict() for v in versions[:limit]]


@router.get(
    "/workflows/{workflow_id}/versions/{version_number}",
    response_model=VersionDetailResponse,
    summary="Get a specific version",
)
async def get_version(
    workflow_id: UUID,
    version_number: int,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "viewer", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    version = await version_service.get_version(workflow_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
    return version.to_dict()


@router.post(
    "/workflows/{workflow_id}/versions/{version_number}/restore",
    response_model=VersionDetailResponse,
    summary="Restore a workflow to a specific version",
)
async def restore_version(
    workflow_id: UUID,
    version_number: int,
    request: RestoreVersionRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "member", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    workflow = await version_service.restore_version(
        workflow_id=workflow_id,
        version_number=version_number,
        restored_by=user_id,
        change_summary=request.change_summary or f"Restored from version {version_number}",
    )
    await repo.save(workflow)

    # Return the restored workflow as a new version
    latest_version = await version_service.get_version(workflow_id, version_number)
    return latest_version.to_dict()


@router.post(
    "/workflows/{workflow_id}/versions/compare",
    response_model=CompareVersionsResponse,
    summary="Compare two workflow versions",
)
async def compare_versions(
    workflow_id: UUID,
    request: CompareVersionsRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    version_service: WorkflowVersionService = Depends(_get_version_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "viewer", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    comparison = await version_service.compare_versions(
        workflow_id, request.version_a, request.version_b
    )
    # Add version details
    v_a = await version_service.get_version(workflow_id, request.version_a)
    v_b = await version_service.get_version(workflow_id, request.version_b)
    if not v_a or not v_b:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    return {
        "version_a": v_a.to_dict(),
        "version_b": v_b.to_dict(),
        "nodes_added": comparison["nodes_added"],
        "nodes_removed": comparison["nodes_removed"],
        "nodes_modified": comparison["nodes_modified"],
        "edges_added": comparison["edges_added"],
        "edges_removed": comparison["edges_removed"],
        "status_changed": comparison["status_changed"],
    }


@router.post(
    "/workflows/{workflow_id}/executions/{execution_id}/replay",
    response_model=ReplayResponse,
    summary="Replay a workflow execution for debugging",
)
async def replay_execution(
    workflow_id: UUID,
    execution_id: UUID,
    request: ReplayExecutionRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    replay_service: WorkflowReplayService = Depends(_get_replay_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "member", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    # Import runner here to avoid circular import
    from app.domain.services.workflow_runner import WorkflowRunner

    runner = WorkflowRunner()
    replay = await replay_service.replay_execution(
        execution_id=execution_id,
        runner=runner,
        context=request.context,
    )
    if not replay:
        raise HTTPException(status_code=404, detail="Execution not found")
    return replay.to_dict()


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}/replay",
    response_model=ReplayResponse,
    summary="Get execution replay data for step-through debugging",
)
async def get_execution_replay(
    workflow_id: UUID,
    execution_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    replay_service: WorkflowReplayService = Depends(_get_replay_service),
) -> dict:
    await require_org_role(request_organization_id(workflow_id, repo, db), "viewer", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    replay = await replay_service.get_replay(execution_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Execution not found")
    return replay.to_dict()


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}/replay/steps",
    response_model=list[dict],
    summary="Get execution steps for step-through debugging",
)
async def get_execution_steps(
    workflow_id: UUID,
    execution_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    repo: WorkflowRepository = Depends(_get_repo),
    replay_service: WorkflowReplayService = Depends(_get_replay_service),
) -> list[dict]:
    await require_org_role(request_organization_id(workflow_id, repo, db), "viewer", user_id, db)
    await require_feature("workflow_automation", request_organization_id(workflow_id, repo, db), "auto", db)

    steps = await replay_service.step_through_execution(execution_id)
    return [s.__dict__ for s in steps]