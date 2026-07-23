"""Approval API routes — CRUD for rules, requests, and decisions.

Endpoints:
  POST   /governance/approval/rules             - Create approval rule
  GET    /governance/approval/rules              - List rules for org
  GET    /governance/approval/rules/{rule_id}    - Get rule
  DELETE /governance/approval/rules/{rule_id}    - Delete rule
  POST   /governance/approval/evaluate           - Evaluate rules against context
  POST   /governance/approval/requests           - Create approval request
  GET    /governance/approval/requests/pending   - List pending requests
  POST   /governance/approval/requests/{id}/decide - Decide (approve/reject)
  POST   /governance/approval/expire             - Expire stale requests
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.governance.approval_use_cases import (
    CreateApprovalRequestUseCase,
    CreateApprovalRuleUseCase,
    DecideApprovalUseCase,
    EvaluateApprovalRulesUseCase,
    ExpireStaleApprovalsUseCase,
    ListPendingApprovalsUseCase,
)
from app.domain.entities.governance.approval import (
    DecisionAction,
    RuleTrigger,
)
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from app.infrastructure.db.repositories.governance.approval_repository import (
    ApprovalDecisionRepositoryImpl,
    ApprovalRequestRepositoryImpl,
    ApprovalRuleRepositoryImpl,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id

router = APIRouter(prefix="/governance/approval", tags=["governance", "approval"])


# ── Request/Response Schemas ───────────────────────────────────────────


class CreateRuleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    trigger: RuleTrigger
    conditions: dict = {}
    approver_roles: list[str] = ["admin"]
    priority: int = Field(default=0, ge=0)
    approval_timeout_hours: int = Field(default=24, ge=1)


class EvaluateRequest(BaseModel):
    organization_id: UUID
    context: dict = {}


class CreateApprovalRequestPayload(BaseModel):
    organization_id: UUID
    rule_id: UUID
    action_type: str
    action_resource_id: str
    action_resource_type: str
    action_summary: str
    action_context: dict = {}
    triggered_by_agent_id: str | None = None
    triggered_by_agent_type: str | None = None


class DecideRequest(BaseModel):
    action: DecisionAction
    reason: str = ""
    conditions: dict = {}


# ── Dependency injection ───────────────────────────────────────────────


async def get_rule_repo(db: AsyncSession = Depends(get_db)) -> ApprovalRuleRepositoryImpl:
    return ApprovalRuleRepositoryImpl(db)


async def get_request_repo(db: AsyncSession = Depends(get_db)) -> ApprovalRequestRepositoryImpl:
    return ApprovalRequestRepositoryImpl(db)


async def get_decision_repo(db: AsyncSession = Depends(get_db)) -> ApprovalDecisionRepositoryImpl:
    return ApprovalDecisionRepositoryImpl(db)


# ── Rule Endpoints ─────────────────────────────────────────────────────


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: CreateRuleRequest,
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
):
    """Create a new approval rule."""
    try:
        uc = CreateApprovalRuleUseCase(repo)
        rule = await uc.execute(
            organization_id=body.organization_id,
            name=body.name,
            trigger=body.trigger,
            conditions=body.conditions,
            approver_roles=body.approver_roles,
            priority=body.priority,
            description=body.description,
            approval_timeout_hours=body.approval_timeout_hours,
        )
        return {
            "id": str(rule.id),
            "name": rule.name,
            "trigger": rule.trigger.value,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules")
async def list_rules(
    organization_id: UUID = Query(...),
    active_only: bool = Query(True),
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
):
    """List approval rules for an organization."""
    rules = await repo.find_by_organization(organization_id, active_only=active_only)
    return {
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "trigger": r.trigger.value,
                "is_active": r.is_active,
                "priority": r.priority,
                "approver_roles": r.approver_roles,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.get("/rules/{rule_id}")
async def get_rule(
    rule_id: UUID,
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
):
    """Get a specific approval rule."""
    rule = await repo.find_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": str(rule.id),
        "name": rule.name,
        "description": rule.description,
        "trigger": rule.trigger.value,
        "is_active": rule.is_active,
        "priority": rule.priority,
        "conditions": rule.conditions,
        "approver_roles": rule.approver_roles,
        "approval_timeout_hours": rule.approval_timeout_hours,
    }


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
):
    """Delete an approval rule."""
    await repo.delete(rule_id)


# ── Evaluation Endpoints ───────────────────────────────────────────────


@router.post("/evaluate")
async def evaluate_rules(
    body: EvaluateRequest,
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
):
    """Evaluate approval rules against an action context."""
    uc = EvaluateApprovalRulesUseCase(repo)
    result = await uc.execute(body.organization_id, body.context)
    return {
        "requires_approval": result.requires_approval,
        "triggered_rule_ids": result.triggered_rule_ids,
        "all_approver_roles": result.all_approver_roles,
        "highest_priority": result.highest_priority,
    }


# ── Request Endpoints ──────────────────────────────────────────────────


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request(
    body: CreateApprovalRequestPayload,
    user_id: UUID = Depends(require_user_id),
    rule_repo: ApprovalRuleRepositoryImpl = Depends(get_rule_repo),
    request_repo: ApprovalRequestRepositoryImpl = Depends(get_request_repo),
):
    """Create an approval request (usually after rule evaluation)."""
    rule = await rule_repo.find_by_id(body.rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    try:
        uc = CreateApprovalRequestUseCase(request_repo)
        request = await uc.execute(
            organization_id=body.organization_id,
            rule=rule,
            action_type=body.action_type,
            action_resource_id=body.action_resource_id,
            action_resource_type=body.action_resource_type,
            action_summary=body.action_summary,
            action_context=body.action_context,
            triggered_by_agent_id=body.triggered_by_agent_id,
            triggered_by_agent_type=body.triggered_by_agent_type,
        )
        return {
            "id": str(request.id),
            "status": request.status.value,
            "action_type": request.action_type,
            "action_summary": request.action_summary,
            "timeout_at": request.timeout_at.isoformat() if request.timeout_at else None,
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/pending")
async def list_pending_requests(
    organization_id: UUID = Query(...),
    role: str | None = Query(None),
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRequestRepositoryImpl = Depends(get_request_repo),
):
    """List pending approval requests."""
    uc = ListPendingApprovalsUseCase(repo)
    requests = await uc.execute(organization_id, role=role)
    return {
        "items": [
            {
                "id": str(r.id),
                "action_type": r.action_type,
                "action_summary": r.action_summary,
                "status": r.status.value,
                "assigned_role": r.assigned_role,
                "timeout_at": r.timeout_at.isoformat() if r.timeout_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in requests
        ],
        "total": len(requests),
    }


@router.post("/requests/{request_id}/decide")
async def decide_request(
    request_id: UUID,
    body: DecideRequest,
    user_id: UUID = Depends(require_user_id),
    request_repo: ApprovalRequestRepositoryImpl = Depends(get_request_repo),
    decision_repo: ApprovalDecisionRepositoryImpl = Depends(get_decision_repo),
):
    """Decide on an approval request (approve/reject)."""
    try:
        uc = DecideApprovalUseCase(request_repo, decision_repo)
        decision = await uc.execute(
            request_id=request_id,
            decided_by=user_id,
            action=body.action,
            reason=body.reason,
            conditions=body.conditions,
        )
        return {
            "id": str(decision.id),
            "request_id": str(decision.request_id),
            "action": decision.action.value,
            "reason": decision.reason,
        }
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expire")
async def expire_stale_requests(
    user_id: UUID = Depends(require_user_id),
    repo: ApprovalRequestRepositoryImpl = Depends(get_request_repo),
):
    """Expire all stale approval requests."""
    uc = ExpireStaleApprovalsUseCase(repo)
    expired = await uc.execute()
    return {
        "expired_count": len(expired),
        "expired_ids": [str(r.id) for r in expired],
    }
