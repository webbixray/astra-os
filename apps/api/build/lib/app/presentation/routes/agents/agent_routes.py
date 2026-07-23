from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.agents.agent_service_bridge import (
    AgentServiceBridge,
    get_agent_service_bridge,
)
from app.application.use_cases.agents.orchestrator import AgentOrchestrator
from app.application.use_cases.agents.tool_registry import ToolRegistry
from app.infrastructure.external_adapters.agents.tool_handlers import register_tools
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class AgentRequest(BaseModel):
    organization_id: UUID
    user_id: UUID | None = None
    message: str


class AgentResponse(BaseModel):
    task_id: str
    response: str
    agents_involved: list[str]
    status: str
    metadata: dict | None = None


def get_orchestrator(db: AsyncSession = Depends(get_db)) -> AgentOrchestrator:
    registry = ToolRegistry()
    register_tools(registry, db)
    return AgentOrchestrator(tool_registry=registry)


# ---------------------------------------------------------------------------
# New endpoints — Full agent orchestrator with ReAct loop
# ---------------------------------------------------------------------------


@router.post("/agents/process")
async def process_with_agents(
    request: AgentRequest,
    bridge: AgentServiceBridge = Depends(get_agent_service_bridge),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Process a user request through the full agent hierarchy."""
    await require_org_role(request.organization_id, "member", user_id, db)
    result = await bridge.process_user_request(
        user_id=user_id,
        organization_id=request.organization_id,
        message=request.message,
    )
    return AgentResponse(
        task_id=result["task_id"],
        response=result["response"],
        agents_involved=result["agents_involved"],
        status=result["status"],
        metadata=result.get("metadata"),
    )


@router.get("/agents")
async def list_agents(
    bridge: AgentServiceBridge = Depends(get_agent_service_bridge),
    user_id: UUID = Depends(require_user_id),
) -> list[dict]:
    """List all registered agent types in the hierarchy."""
    return bridge.get_agents()


@router.get("/agents/hierarchy")
async def get_agent_hierarchy(
    bridge: AgentServiceBridge = Depends(get_agent_service_bridge),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Return the agent hierarchy tree."""
    return bridge.get_hierarchy()


# ---------------------------------------------------------------------------
# Legacy endpoints — kept for backward compatibility
# ---------------------------------------------------------------------------


@router.get("/agents/legacy/tools")
async def list_legacy_tools(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user_id: UUID = Depends(require_user_id),
) -> list[dict]:
    return orchestrator.tool_registry.get_capability_descriptions()
