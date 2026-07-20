"""Workflow Template Routes — API endpoints for workflow templates.

M5 Workflow Engine: Exposes template listing, detail, and instantiation endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class InstantiateTemplateRequest(BaseModel):
    organization_id: UUID
    name: str | None = None
    customizations: dict | None = None


class TemplateSummaryResponse(BaseModel):
    template_id: str
    name: str
    description: str
    category: str
    node_count: int
    edge_count: int
    estimated_duration_minutes: int
    tags: list[str]


class TemplateDetailResponse(TemplateSummaryResponse):
    nodes: list[dict]
    edges: list[dict]


class InstantiatedWorkflowResponse(BaseModel):
    workflow_id: str
    template_id: str
    name: str
    description: str
    node_count: int
    edge_count: int
    organization_id: str
    created_by: str


# ---------------------------------------------------------------------------
# Dependency — lazy import to avoid circular deps
# ---------------------------------------------------------------------------


def _get_registry():
    from app.domain.services.workflow_templates import template_registry

    return template_registry


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[TemplateSummaryResponse],
    summary="List all workflow templates",
)
async def list_templates(
    category: str | None = None,
    user_id: UUID = Depends(require_user_id),
) -> list[dict]:
    registry = _get_registry()
    templates = registry.list_templates(category=category)
    return [t.to_dict() for t in templates]


@router.get(
    "/{template_id}",
    response_model=TemplateDetailResponse,
    summary="Get template details",
)
async def get_template(
    template_id: str,
    user_id: UUID = Depends(require_user_id),
) -> dict:
    registry = _get_registry()
    template = registry.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    result = template.to_dict()
    result["nodes"] = [n.__dict__ for n in template.nodes]
    result["edges"] = [e.__dict__ for e in template.edges]
    return result


@router.post(
    "/{template_id}/instantiate",
    response_model=InstantiatedWorkflowResponse,
    status_code=201,
    summary="Instantiate a template as a new workflow",
)
async def instantiate_template(
    template_id: str,
    request: InstantiateTemplateRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("workflow_automation", request.organization_id, "auto", db)

    registry = _get_registry()
    workflow = registry.instantiate_template(
        template_id=template_id,
        organization_id=request.organization_id,
        created_by=user_id,
        name=request.name,
    )
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    return {
        "workflow_id": str(workflow.id),
        "template_id": template_id,
        "name": workflow.name,
        "description": workflow.description,
        "node_count": len(workflow.nodes),
        "edge_count": len(workflow.edges),
        "organization_id": str(workflow.organization_id),
        "created_by": str(workflow.created_by),
    }
