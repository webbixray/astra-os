from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.ab_test_use_cases import (
    AddVariantUseCase,
    CreateABTestUseCase,
    DetermineWinnerUseCase,
    GetABTestUseCase,
    ListABTestsUseCase,
    RecordVariantMetricsUseCase,
    StartABTestUseCase,
)
from app.application.use_cases.campaigns.budget_use_cases import (
    GetCampaignBudgetUseCase,
    RecordSpendUseCase,
    SetCampaignBudgetUseCase,
)
from app.application.use_cases.campaigns.campaign_use_cases import (
    CreateCampaignUseCase,
    GetCampaignUseCase,
    ListCampaignsUseCase,
    UpdateCampaignUseCase,
)
from app.application.use_cases.campaigns.template_use_cases import (
    CloneCampaignFromTemplateUseCase,
    CreateTemplateUseCase,
    DeleteTemplateUseCase,
    GetTemplateUseCase,
    ListTemplatesUseCase,
)
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.db.repositories.campaigns.ab_test_repository import ABTestRepository
from app.infrastructure.db.repositories.campaigns.campaign_budget_repository import (
    CampaignBudgetRepository,
)
from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
from app.infrastructure.db.repositories.campaigns.campaign_template_repository import (
    CampaignTemplateRepository,
)
from app.infrastructure.metrics import campaigns_created
from app.presentation.dependencies import get_db, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import PaginatedResponse
from app.presentation.schemas.responses import CampaignResponse

router = APIRouter()


class CreateCampaignRequest(BaseModel):
    name: str
    description: str | None = None
    budget_amount: float | None = None
    budget_currency: str = "USD"
    start_date: str | None = None
    end_date: str | None = None
    channels: list[str] = []
    objective: str | None = None
    organization_id: UUID


class UpdateCampaignRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    budget_amount: float | None = None


class SetBudgetRequest(BaseModel):
    total_budget: float = Field(gt=0)
    currency: str = "USD"
    alert_threshold: float = Field(default=80.0, ge=0, le=100)
    period_start: str | None = None
    period_end: str | None = None


class RecordSpendRequest(BaseModel):
    amount: float = Field(gt=0)


class CreateTemplateRequest(BaseModel):
    name: str
    description: str = ""
    channels: list[str] = []
    objective: str | None = None
    budget_amount: float | None = None
    budget_currency: str = "USD"
    default_duration_days: int = 30
    config: dict = {}
    organization_id: UUID


class CloneFromTemplateRequest(BaseModel):
    template_id: UUID
    organization_id: UUID
    name: str
    start_date: str | None = None


class CreateABTestRequest(BaseModel):
    campaign_id: UUID
    name: str
    description: str = ""
    goal_metric: str = "conversion_rate"


class AddVariantRequest(BaseModel):
    name: str
    description: str = ""
    config: dict = {}
    traffic_percent: float = Field(default=50.0, ge=0, le=100)


class RecordMetricsRequest(BaseModel):
    variant_name: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0


async def get_campaign_repo(db: AsyncSession = Depends(get_db)) -> CampaignRepositoryImpl:
    return CampaignRepositoryImpl(db)


async def get_create_use_case(
    repo: CampaignRepositoryImpl = Depends(get_campaign_repo),
) -> CreateCampaignUseCase:
    return CreateCampaignUseCase(repo)


async def get_get_use_case(
    repo: CampaignRepositoryImpl = Depends(get_campaign_repo),
) -> GetCampaignUseCase:
    return GetCampaignUseCase(repo)


async def get_list_use_case(
    repo: CampaignRepositoryImpl = Depends(get_campaign_repo),
) -> ListCampaignsUseCase:
    return ListCampaignsUseCase(repo)


async def get_update_use_case(
    repo: CampaignRepositoryImpl = Depends(get_campaign_repo),
) -> UpdateCampaignUseCase:
    return UpdateCampaignUseCase(repo)


# Budget deps
async def get_budget_repo(db: AsyncSession = Depends(get_db)) -> CampaignBudgetRepository:
    return CampaignBudgetRepository(db)


async def get_set_budget_uc(
    repo: CampaignBudgetRepository = Depends(get_budget_repo),
) -> SetCampaignBudgetUseCase:
    return SetCampaignBudgetUseCase(repo)


async def get_get_budget_uc(
    repo: CampaignBudgetRepository = Depends(get_budget_repo),
) -> GetCampaignBudgetUseCase:
    return GetCampaignBudgetUseCase(repo)


async def get_record_spend_uc(
    repo: CampaignBudgetRepository = Depends(get_budget_repo),
) -> RecordSpendUseCase:
    return RecordSpendUseCase(repo)


# Template deps
async def get_template_repo(db: AsyncSession = Depends(get_db)) -> CampaignTemplateRepository:
    return CampaignTemplateRepository(db)


async def get_create_template_uc(
    repo: CampaignTemplateRepository = Depends(get_template_repo),
) -> CreateTemplateUseCase:
    return CreateTemplateUseCase(repo)


async def get_list_templates_uc(
    repo: CampaignTemplateRepository = Depends(get_template_repo),
) -> ListTemplatesUseCase:
    return ListTemplatesUseCase(repo)


async def get_get_template_uc(
    repo: CampaignTemplateRepository = Depends(get_template_repo),
) -> GetTemplateUseCase:
    return GetTemplateUseCase(repo)


async def get_delete_template_uc(
    repo: CampaignTemplateRepository = Depends(get_template_repo),
) -> DeleteTemplateUseCase:
    return DeleteTemplateUseCase(repo)


async def get_clone_uc(
    trepo: CampaignTemplateRepository = Depends(get_template_repo),
    crepo: CampaignRepositoryImpl = Depends(get_campaign_repo),
) -> CloneCampaignFromTemplateUseCase:
    return CloneCampaignFromTemplateUseCase(trepo, crepo)


# AB test deps
async def get_abtest_repo(db: AsyncSession = Depends(get_db)) -> ABTestRepository:
    return ABTestRepository(db)


async def get_create_abtest_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> CreateABTestUseCase:
    return CreateABTestUseCase(repo)


async def get_list_abtests_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> ListABTestsUseCase:
    return ListABTestsUseCase(repo)


async def get_get_abtest_uc(repo: ABTestRepository = Depends(get_abtest_repo)) -> GetABTestUseCase:
    return GetABTestUseCase(repo)


async def get_add_variant_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> AddVariantUseCase:
    return AddVariantUseCase(repo)


async def get_start_abtest_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> StartABTestUseCase:
    return StartABTestUseCase(repo)


async def get_determine_winner_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> DetermineWinnerUseCase:
    return DetermineWinnerUseCase(repo)


async def get_record_metrics_uc(
    repo: ABTestRepository = Depends(get_abtest_repo),
) -> RecordVariantMetricsUseCase:
    return RecordVariantMetricsUseCase(repo)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new campaign")
async def create_campaign(
    request: CreateCampaignRequest,
    use_case: CreateCampaignUseCase = Depends(get_create_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    try:
        campaign = await use_case.execute(
            organization_id=request.organization_id,
            name=request.name,
            created_by=user_id,
            description=request.description,
            budget_amount=request.budget_amount,
            budget_currency=request.budget_currency,
            start_date=request.start_date,
            end_date=request.end_date,
            channels=request.channels,
            objective=request.objective,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    campaigns_created.inc()
    return CampaignResponse(
        id=campaign.id,
        organization_id=campaign.organization_id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        budget_amount=campaign.budget_amount,
        budget_currency=campaign.budget_currency,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=campaign.end_date.isoformat() if campaign.end_date else None,
        channels=campaign.channels,
        objective=campaign.objective,
        created_by=campaign.created_by,
        ai_generated=campaign.ai_generated,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get("/{campaign_id}", summary="Get a campaign by ID")
async def get_campaign(
    campaign_id: UUID,
    use_case: GetCampaignUseCase = Depends(get_get_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign = await use_case.execute(campaign_id=campaign_id)
        await require_org_role(campaign.organization_id, "viewer", user_id, db)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        ) from None
    return CampaignResponse(
        id=campaign.id,
        organization_id=campaign.organization_id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        budget_amount=campaign.budget_amount,
        budget_currency=campaign.budget_currency,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=campaign.end_date.isoformat() if campaign.end_date else None,
        channels=campaign.channels,
        objective=campaign.objective,
        created_by=campaign.created_by,
        ai_generated=campaign.ai_generated,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get("", summary="List all campaigns")
async def list_campaigns(
    org_id: UUID = Query(..., alias="organization_id"),
    status: str | None = Query(None),
    use_case: ListCampaignsUseCase = Depends(get_list_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse[CampaignResponse]:
    await require_org_role(org_id, "viewer", user_id, db)
    campaigns = await use_case.execute(org_id=org_id, status=status)
    items = [
        CampaignResponse(
            id=c.id,
            organization_id=c.organization_id,
            name=c.name,
            description=c.description,
            status=c.status,
            budget_amount=c.budget_amount,
            budget_currency=c.budget_currency,
            start_date=c.start_date.isoformat() if c.start_date else None,
            end_date=c.end_date.isoformat() if c.end_date else None,
            channels=c.channels,
            objective=c.objective,
            created_by=c.created_by,
            ai_generated=c.ai_generated,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in campaigns
    ]
    total = len(items)
    page = pagination["page"]
    limit = pagination["limit"]
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    )


@router.patch("/{campaign_id}", summary="Update a campaign")
async def update_campaign(
    campaign_id: UUID,
    request: UpdateCampaignRequest,
    use_case: UpdateCampaignUseCase = Depends(get_update_use_case),
    get_campaign: GetCampaignUseCase = Depends(get_get_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        existing = await get_campaign.execute(campaign_id=campaign_id)
        await require_org_role(existing.organization_id, "member", user_id, db)
        campaign = await use_case.execute(
            campaign_id=campaign_id,
            name=request.name,
            description=request.description,
            status=request.status,
            budget_amount=request.budget_amount,
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        ) from None
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return CampaignResponse(
        id=campaign.id,
        organization_id=campaign.organization_id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        budget_amount=campaign.budget_amount,
        budget_currency=campaign.budget_currency,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=campaign.end_date.isoformat() if campaign.end_date else None,
        channels=campaign.channels,
        objective=campaign.objective,
        created_by=campaign.created_by,
        ai_generated=campaign.ai_generated,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


# ── Budget endpoints ──────────────────────────────────────────────────────────


@router.get("/{campaign_id}/budget", summary="Get campaign budget details")
async def get_campaign_budget(
    campaign_id: UUID,
    use_case: GetCampaignBudgetUseCase = Depends(get_get_budget_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaign = await campaign_repo.find_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        ) from None
    await require_org_role(campaign.organization_id, "viewer", user_id, db)
    try:
        budget = await use_case.execute(campaign_id=campaign_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        ) from None
    return {
        "id": str(budget.id),
        "campaign_id": str(budget.campaign_id),
        "total_budget": budget.total_budget,
        "spent": budget.spent,
        "remaining": budget.remaining,
        "spend_pct": budget.spend_pct,
        "currency": budget.currency,
        "alert_threshold": budget.alert_threshold,
        "is_alert_triggered": budget.is_alert_triggered,
        "period_start": budget.period_start.isoformat() if budget.period_start else None,
        "period_end": budget.period_end.isoformat() if budget.period_end else None,
    }


@router.put("/{campaign_id}/budget", status_code=status.HTTP_200_OK, summary="Set campaign budget")
async def set_campaign_budget(
    campaign_id: UUID,
    request: SetBudgetRequest,
    use_case: SetCampaignBudgetUseCase = Depends(get_set_budget_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaign = await campaign_repo.find_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await require_org_role(campaign.organization_id, "member", user_id, db)
    try:
        budget = await use_case.execute(
            campaign_id=campaign_id,
            total_budget=request.total_budget,
            currency=request.currency,
            alert_threshold=request.alert_threshold,
            period_start=request.period_start,
            period_end=request.period_end,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return {
        "id": str(budget.id),
        "campaign_id": str(budget.campaign_id),
        "total_budget": budget.total_budget,
        "spent": budget.spent,
        "remaining": budget.remaining,
        "currency": budget.currency,
        "alert_threshold": budget.alert_threshold,
    }


@router.post(
    "/{campaign_id}/budget/spend", status_code=status.HTTP_200_OK, summary="Record campaign spend"
)
async def record_campaign_spend(
    campaign_id: UUID,
    request: RecordSpendRequest,
    use_case: RecordSpendUseCase = Depends(get_record_spend_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaign = await campaign_repo.find_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        ) from None
    await require_org_role(campaign.organization_id, "member", user_id, db)
    try:
        budget = await use_case.execute(campaign_id=campaign_id, amount=request.amount)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        ) from None
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return {
        "spent": budget.spent,
        "remaining": budget.remaining,
        "spend_pct": budget.spend_pct,
    }


# ── Template endpoints ────────────────────────────────────────────────────────


@router.post(
    "/templates", status_code=status.HTTP_201_CREATED, summary="Create a campaign template"
)
async def create_template(
    request: CreateTemplateRequest,
    use_case: CreateTemplateUseCase = Depends(get_create_template_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    template = await use_case.execute(
        organization_id=request.organization_id,
        name=request.name,
        created_by=user_id,
        description=request.description,
        channels=request.channels,
        objective=request.objective,
        budget_amount=request.budget_amount,
        budget_currency=request.budget_currency,
        default_duration_days=request.default_duration_days,
        config=request.config,
    )
    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "channels": template.channels,
        "objective": template.objective,
        "budget_amount": template.budget_amount,
        "budget_currency": template.budget_currency,
        "default_duration_days": template.default_duration_days,
    }


@router.get("/templates", summary="List all campaign templates")
async def list_templates(
    org_id: UUID = Query(..., alias="organization_id"),
    use_case: ListTemplatesUseCase = Depends(get_list_templates_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(org_id, "viewer", user_id, db)
    templates = await use_case.execute(org_id=org_id)
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "channels": t.channels,
            "objective": t.objective,
            "budget_amount": t.budget_amount,
            "budget_currency": t.budget_currency,
            "default_duration_days": t.default_duration_days,
            "created_by": str(t.created_by),
        }
        for t in templates
    ]


@router.get("/templates/{template_id}", summary="Get a template by ID")
async def get_template(
    template_id: UUID,
    use_case: GetTemplateUseCase = Depends(get_get_template_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        template = await use_case.execute(template_id=template_id)
        await require_org_role(template.organization_id, "viewer", user_id, db)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        ) from None
    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "channels": template.channels,
        "objective": template.objective,
        "budget_amount": template.budget_amount,
        "budget_currency": template.budget_currency,
        "default_duration_days": template.default_duration_days,
        "config": template.config,
    }


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign template",
)
async def delete_template(
    template_id: UUID,
    get_template: GetTemplateUseCase = Depends(get_get_template_uc),
    delete_template_uc: DeleteTemplateUseCase = Depends(get_delete_template_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        template = await get_template.execute(template_id=template_id)
        await require_org_role(template.organization_id, "member", user_id, db)
        await delete_template_uc.execute(template_id=template_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        ) from None


@router.post(
    "/from-template", status_code=status.HTTP_201_CREATED, summary="Clone campaign from template"
)
async def clone_from_template(
    request: CloneFromTemplateRequest,
    use_case: CloneCampaignFromTemplateUseCase = Depends(get_clone_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    try:
        campaign = await use_case.execute(
            template_id=request.template_id,
            organization_id=request.organization_id,
            name=request.name,
            created_by=user_id,
            start_date=request.start_date,
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        ) from None
    return CampaignResponse(
        id=campaign.id,
        organization_id=campaign.organization_id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        budget_amount=campaign.budget_amount,
        budget_currency=campaign.budget_currency,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=None,
        channels=campaign.channels,
        objective=campaign.objective,
        created_by=campaign.created_by,
        ai_generated=campaign.ai_generated,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


# ── A/B test endpoints ────────────────────────────────────────────────────────


@router.post(
    "/{campaign_id}/ab-tests", status_code=status.HTTP_201_CREATED, summary="Create an A/B test"
)
async def create_ab_test(
    campaign_id: UUID,
    request: CreateABTestRequest,
    use_case: CreateABTestUseCase = Depends(get_create_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaign = await campaign_repo.find_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await require_org_role(campaign.organization_id, "member", user_id, db)
    try:
        test = await use_case.execute(
            campaign_id=campaign_id,
            organization_id=campaign.organization_id,
            name=request.name,
            created_by=user_id,
            description=request.description,
            goal_metric=request.goal_metric,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return {
        "id": str(test.id),
        "campaign_id": str(test.campaign_id),
        "name": test.name,
        "description": test.description,
        "status": test.status,
        "goal_metric": test.goal_metric,
    }


@router.get("/{campaign_id}/ab-tests", summary="List A/B tests for campaign")
async def list_ab_tests(
    campaign_id: UUID,
    use_case: ListABTestsUseCase = Depends(get_list_abtests_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaign = await campaign_repo.find_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        ) from None
    await require_org_role(campaign.organization_id, "viewer", user_id, db)
    tests = await use_case.execute(campaign_id=campaign_id)
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "status": t.status,
            "goal_metric": t.goal_metric,
            "winner_variant_id": str(t.winner_variant_id) if t.winner_variant_id else None,
            "variants_count": len(t.variants),
            "created_at": t.created_at.isoformat(),
        }
        for t in tests
    ]


@router.get("/ab-tests/{test_id}", summary="Get A/B test details")
async def get_ab_test(
    test_id: UUID,
    use_case: GetABTestUseCase = Depends(get_get_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        test = await use_case.execute(test_id=test_id)
        from app.infrastructure.db.repositories.campaigns.campaign_repository import (
            CampaignRepositoryImpl,
        )

        campaign_repo = CampaignRepositoryImpl(db)
        campaign = await campaign_repo.find_by_id(test.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            ) from None
        await require_org_role(campaign.organization_id, "viewer", user_id, db)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AB test not found"
        ) from None
    return {
        "id": str(test.id),
        "campaign_id": str(test.campaign_id),
        "name": test.name,
        "description": test.description,
        "status": test.status,
        "goal_metric": test.goal_metric,
        "winner_variant_id": str(test.winner_variant_id) if test.winner_variant_id else None,
        "start_date": test.start_date.isoformat() if test.start_date else None,
        "end_date": test.end_date.isoformat() if test.end_date else None,
        "variants": [
            {
                "id": str(v.id),
                "name": v.name,
                "description": v.description,
                "traffic_percent": v.traffic_percent,
                "impressions": v.impressions,
                "clicks": v.clicks,
                "conversions": v.conversions,
                "spend": v.spend,
                "ctr": v.ctr,
                "conversion_rate": v.conversion_rate,
                "cpa": v.cpa,
            }
            for v in test.variants
        ],
    }


@router.post(
    "/ab-tests/{test_id}/variants",
    status_code=status.HTTP_201_CREATED,
    summary="Add variant to A/B test",
)
async def add_variant(
    test_id: UUID,
    request: AddVariantRequest,
    use_case: AddVariantUseCase = Depends(get_add_variant_uc),
    get_abtest: GetABTestUseCase = Depends(get_get_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        existing_test = await get_abtest.execute(test_id=test_id)
        from app.infrastructure.db.repositories.campaigns.campaign_repository import (
            CampaignRepositoryImpl,
        )

        campaign_repo = CampaignRepositoryImpl(db)
        campaign = await campaign_repo.find_by_id(existing_test.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            ) from None
        await require_org_role(campaign.organization_id, "member", user_id, db)
        test = await use_case.execute(
            test_id=test_id,
            name=request.name,
            description=request.description,
            config=request.config,
            traffic_percent=request.traffic_percent,
        )
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    return {
        "id": str(test.id),
        "status": test.status,
        "variants": [
            {
                "id": str(v.id),
                "name": v.name,
                "traffic_percent": v.traffic_percent,
            }
            for v in test.variants
        ],
    }


@router.post("/ab-tests/{test_id}/start", summary="Start an A/B test")
async def start_ab_test(
    test_id: UUID,
    use_case: StartABTestUseCase = Depends(get_start_abtest_uc),
    get_abtest: GetABTestUseCase = Depends(get_get_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        existing_test = await get_abtest.execute(test_id=test_id)
        from app.infrastructure.db.repositories.campaigns.campaign_repository import (
            CampaignRepositoryImpl,
        )

        campaign_repo = CampaignRepositoryImpl(db)
        campaign = await campaign_repo.find_by_id(existing_test.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            ) from None
        await require_org_role(campaign.organization_id, "member", user_id, db)
        test = await use_case.execute(test_id=test_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    return {
        "id": str(test.id),
        "status": test.status,
        "start_date": test.start_date.isoformat() if test.start_date else None,
    }


@router.post("/ab-tests/{test_id}/determine-winner", summary="Determine A/B test winner")
async def determine_winner(
    test_id: UUID,
    use_case: DetermineWinnerUseCase = Depends(get_determine_winner_uc),
    get_abtest: GetABTestUseCase = Depends(get_get_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        existing_test = await get_abtest.execute(test_id=test_id)
        from app.infrastructure.db.repositories.campaigns.campaign_repository import (
            CampaignRepositoryImpl,
        )

        campaign_repo = CampaignRepositoryImpl(db)
        campaign = await campaign_repo.find_by_id(existing_test.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            ) from None
        await require_org_role(campaign.organization_id, "member", user_id, db)
        test = await use_case.execute(test_id=test_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AB test not found"
        ) from None
    return {
        "id": str(test.id),
        "status": test.status,
        "winner_variant_id": str(test.winner_variant_id) if test.winner_variant_id else None,
        "end_date": test.end_date.isoformat() if test.end_date else None,
    }


@router.post("/ab-tests/{test_id}/metrics", summary="Record variant metrics")
async def record_variant_metrics(
    test_id: UUID,
    request: RecordMetricsRequest,
    use_case: RecordVariantMetricsUseCase = Depends(get_record_metrics_uc),
    get_abtest: GetABTestUseCase = Depends(get_get_abtest_uc),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        existing_test = await get_abtest.execute(test_id=test_id)
        from app.infrastructure.db.repositories.campaigns.campaign_repository import (
            CampaignRepositoryImpl,
        )

        campaign_repo = CampaignRepositoryImpl(db)
        campaign = await campaign_repo.find_by_id(existing_test.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            ) from None
        await require_org_role(campaign.organization_id, "member", user_id, db)
        test = await use_case.execute(
            test_id=test_id,
            variant_name=request.variant_name,
            impressions=request.impressions,
            clicks=request.clicks,
            conversions=request.conversions,
            spend=request.spend,
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found"
        ) from None
    return {"id": str(test.id), "status": "metrics_recorded"}
