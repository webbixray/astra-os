from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.automation_service import AutomationService
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateBudgetRuleRequest(BaseModel):
    campaign_id: UUID
    name: str
    strategy: str = "equal"
    allocations: dict = {}


class CreateBidRuleRequest(BaseModel):
    ad_account_id: UUID
    name: str
    strategy: str = "target_cpa"
    target_value: float = 0.0
    min_bid: float = 0.0
    max_bid: float = 0.0


class CreateSegmentRequest(BaseModel):
    name: str
    source: str = "custom"
    criteria: dict = {}


class CreateRuleRequest(BaseModel):
    name: str
    trigger_type: str
    action_type: str
    trigger_config: dict = {}
    action_config: dict = {}
    description: str = ""


def get_service(db: AsyncSession = Depends(get_db)) -> AutomationService:
    return AutomationService(db)


# ── Budget Allocation ────────────────────────────────────────────────────────

@router.post("/automation/budget-rules", status_code=status.HTTP_201_CREATED, summary="Create a budget allocation rule")
async def create_budget_rule(
    request: CreateBudgetRuleRequest,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    try:
        rule = await service.create_budget_rule(
            org_id=organization_id, campaign_id=request.campaign_id,
            name=request.name, strategy=request.strategy,
            allocations=request.allocations,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(rule.id), "name": rule.name, "strategy": rule.strategy}


@router.get("/automation/budget-rules", summary="List budget allocation rules")
async def list_budget_rules(
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_budget_rules(org_id=organization_id)


@router.post("/automation/budget-rules/{rule_id}/calculate", summary="Calculate budget allocation")
async def calculate_allocation(
    rule_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        return await service.calculate_allocation(rule_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found") from None


@router.delete("/automation/budget-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a budget rule")
async def delete_budget_rule(
    rule_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_budget_rule(rule_id)


# ── Bid Optimization ─────────────────────────────────────────────────────────

@router.post("/automation/bid-rules", status_code=status.HTTP_201_CREATED, summary="Create a bid optimization rule")
async def create_bid_rule(
    request: CreateBidRuleRequest,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    try:
        rule = await service.create_bid_rule(
            org_id=organization_id, ad_account_id=request.ad_account_id,
            name=request.name, strategy=request.strategy,
            target_value=request.target_value,
            min_bid=request.min_bid, max_bid=request.max_bid,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(rule.id), "name": rule.name, "strategy": rule.strategy}


@router.get("/automation/bid-rules", summary="List bid optimization rules")
async def list_bid_rules(
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_bid_rules(org_id=organization_id)


@router.post("/automation/bid-rules/{rule_id}/optimize", summary="Optimize bid for rule")
async def optimize_bid(
    rule_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        return await service.optimize_bid(rule_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found") from None


@router.delete("/automation/bid-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a bid rule")
async def delete_bid_rule(
    rule_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_bid_rule(rule_id)


# ── Audience Segmentation ────────────────────────────────────────────────────

@router.post("/automation/audience-segments", status_code=status.HTTP_201_CREATED, summary="Create an audience segment")
async def create_audience_segment(
    request: CreateSegmentRequest,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    try:
        segment = await service.create_audience_segment(
            org_id=organization_id, name=request.name,
            source=request.source, criteria=request.criteria,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(segment.id), "name": segment.name,
            "source": segment.source, "predicted_size": segment.predicted_size}


@router.get("/automation/audience-segments", summary="List audience segments")
async def list_audience_segments(
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_audience_segments(org_id=organization_id)


@router.post("/automation/audience-segments/{segment_id}/predict", summary="Predict audience size")
async def predict_audience(
    segment_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        return await service.predict_audience(segment_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found") from None


@router.delete("/automation/audience-segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an audience segment")
async def delete_audience_segment(
    segment_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_audience_segment(segment_id)


# ── Content Recommendations ──────────────────────────────────────────────────

@router.post("/automation/recommendations/generate", summary="Generate content recommendations")
async def generate_recommendations(
    organization_id: UUID = Query(...),
    campaign_id: UUID | None = Query(None),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    recs = await service.generate_recommendations(
        org_id=organization_id, campaign_id=campaign_id,
    )
    return [
        {"id": str(r.id), "type": r.recommendation_type,
         "title": r.title, "confidence_score": r.confidence_score}
        for r in recs
    ]


@router.get("/automation/recommendations", summary="List content recommendations")
async def list_recommendations(
    organization_id: UUID = Query(...),
    type: str | None = Query(None, alias="type"),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_recommendations(org_id=organization_id, rec_type=type)


@router.post("/automation/recommendations/{rec_id}/apply", summary="Apply a recommendation")
async def apply_recommendation(
    rec_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "member", user_id, db)
    try:
        rec = await service.apply_recommendation(rec_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found") from None
    return {"id": str(rec.id), "applied": rec.applied}


# ── Automation Rules Engine ──────────────────────────────────────────────────

@router.post("/automation/rules", status_code=status.HTTP_201_CREATED, summary="Create an automation rule")
async def create_automation_rule(
    request: CreateRuleRequest,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    try:
        rule = await service.create_rule(
            org_id=organization_id, name=request.name,
            trigger_type=request.trigger_type, action_type=request.action_type,
            trigger_config=request.trigger_config,
            action_config=request.action_config,
            description=request.description, created_by=user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(rule.id), "name": rule.name,
            "trigger_type": rule.trigger_type, "action_type": rule.action_type}


@router.get("/automation/rules", summary="List automation rules")
async def list_automation_rules(
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_rules(org_id=organization_id)


@router.patch("/automation/rules/{rule_id}/toggle", summary="Toggle automation rule enabled state")
async def toggle_automation_rule(
    rule_id: UUID,
    enabled: bool = Query(...),
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "member", user_id, db)
    try:
        rule = await service.toggle_rule(rule_id, enabled)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found") from None
    return {"id": str(rule.id), "enabled": rule.enabled}


@router.post("/automation/rules/evaluate", summary="Evaluate all automation rules")
async def evaluate_automation_rules(
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.evaluate_rules(org_id=organization_id)


@router.delete("/automation/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an automation rule")
async def delete_automation_rule(
    rule_id: UUID,
    organization_id: UUID = Query(...),
    service: AutomationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_rule(rule_id)
