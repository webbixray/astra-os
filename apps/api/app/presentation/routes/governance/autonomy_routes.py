"""Autonomy API routes — config management, action checking, agent actions.

Endpoints:
  GET    /governance/autonomy/config             - Get autonomy config
  PUT    /governance/autonomy/config             - Update autonomy config
  POST   /governance/autonomy/check              - Check if action is permitted
  POST   /governance/autonomy/actions            - Record an agent action
  GET    /governance/autonomy/actions            - List agent actions
  GET    /governance/autonomy/actions/{id}       - Get specific action
  GET    /governance/autonomy/explain/{id}       - Explain an action
  GET    /governance/autonomy/explain/{id}/replay - Decision replay
  GET    /governance/autonomy/summary            - Audit summary for org
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.governance.autonomy_use_cases import (
    AgentActionRepository,
    AutonomyConfigRepository,
    CheckAgentActionUseCase,
    GetAgentActionsUseCase,
    GetAutonomyConfigUseCase,
    GetExplainabilityReportUseCase,
    RecordAgentActionUseCase,
    UpdateAutonomyConfigUseCase,
)
from app.domain.entities.governance.autonomy import AutonomyLevel
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from app.infrastructure.db.repositories.governance.autonomy_repository import (
    AgentActionRepositoryImpl,
    AutonomyConfigRepositoryImpl,
)
from app.presentation.dependencies import get_db

router = APIRouter(prefix="/governance/autonomy", tags=["governance", "autonomy"])


# ── Request/Response Schemas ───────────────────────────────────────────


class UpdateConfigRequest(BaseModel):
    organization_id: UUID
    default_level: int | None = Field(None, ge=0, le=2)
    agent_levels: dict[str, int] | None = None
    action_overrides: dict[str, int] | None = None
    auto_approve_spend_limit: float | None = Field(None, ge=0)
    auto_execute_channels: list[str] | None = None


class CheckActionRequest(BaseModel):
    organization_id: UUID
    action_name: str
    agent_type: str
    agent_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    context: dict = {}
    spend_amount: float = 0.0


class RecordActionRequest(BaseModel):
    organization_id: UUID
    agent_id: str
    agent_type: str
    action_name: str
    resource_type: str = ""
    resource_id: str = ""
    reasoning: str = ""
    reasoning_trace: list[dict] = []
    autonomy_level: int = Field(default=0, ge=0, le=2)
    was_auto_executed: bool = False
    approval_request_id: str | None = None
    success: bool = True
    error_message: str = ""
    result: dict = {}
    tokens_used: int = 0
    cost_usd: float = 0.0
    model_used: str = ""
    details: dict = {}


# ── Dependency injection ───────────────────────────────────────────────


async def get_config_repo(db: AsyncSession = Depends(get_db)) -> AutonomyConfigRepositoryImpl:
    return AutonomyConfigRepositoryImpl(db)


async def get_action_repo(db: AsyncSession = Depends(get_db)) -> AgentActionRepositoryImpl:
    return AgentActionRepositoryImpl(db)


# ── Config Endpoints ───────────────────────────────────────────────────


@router.get("/config")
async def get_config(
    organization_id: UUID = Query(...),
    repo: AutonomyConfigRepositoryImpl = Depends(get_config_repo),
):
    """Get autonomy configuration for an organization."""
    uc = GetAutonomyConfigUseCase(repo)
    config = await uc.execute(organization_id)
    return {
        "id": str(config.id),
        "organization_id": str(config.organization_id),
        "default_level": config.default_level.value,
        "agent_levels": {k: v.value for k, v in config.agent_levels.items()},
        "action_overrides": {k: v.value for k, v in config.action_overrides.items()},
        "auto_approve_spend_limit": config.auto_approve_spend_limit,
        "auto_approve_currency": config.auto_approve_currency,
        "auto_execute_channels": config.auto_execute_channels,
    }


@router.put("/config")
async def update_config(
    body: UpdateConfigRequest,
    repo: AutonomyConfigRepositoryImpl = Depends(get_config_repo),
):
    """Update autonomy configuration."""
    try:
        uc = UpdateAutonomyConfigUseCase(repo)
        agent_levels = None
        if body.agent_levels is not None:
            agent_levels = {k: AutonomyLevel(v) for k, v in body.agent_levels.items()}

        action_overrides = None
        if body.action_overrides is not None:
            action_overrides = {k: AutonomyLevel(v) for k, v in body.action_overrides.items()}

        config = await uc.execute(
            organization_id=body.organization_id,
            default_level=AutonomyLevel(body.default_level) if body.default_level is not None else None,
            agent_levels=agent_levels,
            action_overrides=action_overrides,
            auto_approve_spend_limit=body.auto_approve_spend_limit,
            auto_execute_channels=body.auto_execute_channels,
        )
        return {
            "id": str(config.id),
            "default_level": config.default_level.value,
            "agent_levels": {k: v.value for k, v in config.agent_levels.items()},
            "auto_approve_spend_limit": config.auto_approve_spend_limit,
        }
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Action Check Endpoint ──────────────────────────────────────────────


@router.post("/check")
async def check_action(
    body: CheckActionRequest,
    config_repo: AutonomyConfigRepositoryImpl = Depends(get_config_repo),
):
    """Check if an agent action is permitted before execution."""
    uc = CheckAgentActionUseCase(config_repo)
    result = await uc.execute(
        organization_id=body.organization_id,
        action_name=body.action_name,
        agent_type=body.agent_type,
        agent_id=body.agent_id,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        context=body.context,
        spend_amount=body.spend_amount,
    )
    return result.to_dict()


# ── Action Recording Endpoints ─────────────────────────────────────────


@router.post("/actions", status_code=status.HTTP_201_CREATED)
async def record_action(
    body: RecordActionRequest,
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """Record an agent action for audit."""
    from app.domain.entities.governance.autonomy import AutonomyLevel
    from uuid import UUID as _UUID

    uc = RecordAgentActionUseCase(repo)
    approval_id = _UUID(body.approval_request_id) if body.approval_request_id else None
    action = await uc.execute(
        organization_id=body.organization_id,
        agent_id=body.agent_id,
        agent_type=body.agent_type,
        action_name=body.action_name,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        reasoning=body.reasoning,
        reasoning_trace=body.reasoning_trace,
        autonomy_level=AutonomyLevel(body.autonomy_level),
        was_auto_executed=body.was_auto_executed,
        approval_request_id=approval_id,
        success=body.success,
        error_message=body.error_message,
        result=body.result,
        tokens_used=body.tokens_used,
        cost_usd=body.cost_usd,
        model_used=body.model_used,
        details=body.details,
    )
    return {
        "id": str(action.id),
        "action": action.action,
        "success": action.success,
        "was_auto_executed": action.was_auto_executed,
        "created_at": action.created_at.isoformat(),
    }


@router.get("/actions")
async def list_actions(
    organization_id: UUID = Query(...),
    agent_type: str | None = Query(None),
    action_name: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """List agent actions for an organization."""
    uc = GetAgentActionsUseCase(repo)
    actions = await uc.execute(
        organization_id,
        agent_type=agent_type,
        action_name=action_name,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [
            {
                "id": str(a.id),
                "agent_type": a.agent_type,
                "action": a.action,
                "resource_type": a.resource_type,
                "success": a.success,
                "was_auto_executed": a.was_auto_executed,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
        "total": len(actions),
    }


@router.get("/actions/{action_id}")
async def get_action(
    action_id: UUID,
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """Get a specific agent action."""
    uc = GetAgentActionsUseCase(repo)
    try:
        action = await uc.get_by_id(action_id)
        return {
            "id": str(action.id),
            "agent_type": action.agent_type,
            "agent_id": action.agent_id,
            "action": action.action,
            "resource_type": action.resource_type,
            "resource_id": action.resource_id,
            "reasoning": action.reasoning,
            "reasoning_trace": action.reasoning_trace,
            "autonomy_level": action.autonomy_level.value,
            "was_auto_executed": action.was_auto_executed,
            "success": action.success,
            "error_message": action.error_message,
            "tokens_used": action.tokens_used,
            "cost_usd": action.cost_usd,
            "model_used": action.model_used,
            "created_at": action.created_at.isoformat(),
        }
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Explainability Endpoints ───────────────────────────────────────────


@router.get("/explain/{action_id}")
async def explain_action(
    action_id: UUID,
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """Generate a natural-language explanation of an agent action."""
    uc = GetExplainabilityReportUseCase(repo)
    try:
        explanation = await uc.explain_action(action_id)
        return {
            "action_id": explanation.action_id,
            "one_line": explanation.one_line,
            "paragraph": explanation.paragraph,
            "detailed": explanation.detailed,
            "reasoning_steps": explanation.reasoning_steps,
            "autonomy_context": explanation.autonomy_context,
            "outcome": explanation.outcome,
        }
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/explain/{action_id}/replay")
async def replay_decision(
    action_id: UUID,
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """Step-by-step decision replay for an action."""
    uc = GetExplainabilityReportUseCase(repo)
    try:
        steps = await uc.replay_decision(action_id)
        return {"action_id": str(action_id), "steps": steps}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary")
async def audit_summary(
    organization_id: UUID = Query(...),
    repo: AgentActionRepositoryImpl = Depends(get_action_repo),
):
    """Audit summary for all actions in an organization."""
    uc = GetExplainabilityReportUseCase(repo)
    return await uc.generate_audit_summary(organization_id)
