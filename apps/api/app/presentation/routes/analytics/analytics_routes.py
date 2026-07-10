from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.analytics.analytics_service import AnalyticsService
from app.infrastructure.db.repositories.advertising.advertising_repository import (
    AdAccountRepository,
)
from app.infrastructure.db.repositories.campaigns.campaign_repository import (
    CampaignRepositoryImpl,
)
from app.infrastructure.db.repositories.content.content_repository import (
    ContentRepositoryImpl,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class OverviewResponse(BaseModel):
    total_campaigns: int
    active_campaigns: int
    draft_campaigns: int
    completed_campaigns: int
    total_content: int
    published_content: int
    total_budget: float
    status_breakdown: dict


class CampaignPerformanceItem(BaseModel):
    id: str
    name: str
    status: str
    budget: float
    channels: list[str]
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    roi: float


async def get_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    campaign_repo = CampaignRepositoryImpl(db)
    content_repo = ContentRepositoryImpl(db)
    return AnalyticsService(campaign_repo, content_repo)


@router.get("/analytics/overview", response_model=OverviewResponse)
async def get_overview(
    organization_id: UUID,
    service: AnalyticsService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_overview(organization_id)


@router.get("/analytics/campaigns", response_model=list[CampaignPerformanceItem])
async def get_campaign_performance(
    organization_id: UUID,
    service: AnalyticsService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_campaign_performance(organization_id)


@router.get("/analytics/ads")
async def get_ad_performance(
    organization_id: UUID = Query(...),
    service: AnalyticsService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    ad_account_repo = AdAccountRepository(db)
    accounts = await ad_account_repo.find_by_organization(organization_id)
    connected_accounts = [
        {"platform": a.platform, "platform_account_id": a.platform_account_id}
        for a in accounts
    ]
    return await service.get_ad_performance(connected_accounts)
