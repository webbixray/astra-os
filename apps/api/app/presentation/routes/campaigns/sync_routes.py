"""Campaign Sync API — pull performance data from ad platforms.

Endpoints:
    POST /sync/{account_id}           — Sync all campaigns from platform
    POST /sync/{account_id}/campaign/{platform_campaign_id} — Sync single campaign
    GET  /sync/{account_id}/insights  — Refresh insights from platform
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class SyncAllRequest(BaseModel):
    platform: str = "meta"


class SyncSingleRequest(BaseModel):
    platform: str = "meta"
    account_id: str = ""


class RefreshInsightsRequest(BaseModel):
    platform: str = "meta"
    account_id: str = ""


def _get_adapter(platform: str, credentials: dict | None = None):
    """Factory: get the right adapter for the platform."""
    from app.infrastructure.external_adapters.adplatforms.base_adapter import (
        AdPlatformFactory,
    )

    factory = AdPlatformFactory()
    return factory.create(platform, credentials)


@router.post(
    "/{account_id}/sync-all",
    summary="Sync all campaigns from an ad platform",
)
async def sync_all_campaigns(
    account_id: UUID,
    request: SyncAllRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pull all campaigns from the specified platform and sync locally."""
    try:
        from app.application.use_cases.campaigns.sync_use_cases import (
            SyncAllCampaignsUseCase,
        )
        from app.infrastructure.db.repositories.campaigns.sync_repository import (
            AdCampaignRepoImpl,
            AdInsightRepoImpl,
        )

        # Resolve org
        from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found") from None
        org_id = user.organization_id

        await require_org_role(org_id, "member", user_id, db)

        adapter = _get_adapter(request.platform)
        campaign_repo = AdCampaignRepoImpl(db)
        insight_repo = AdInsightRepoImpl(db)

        use_case = SyncAllCampaignsUseCase(
            ad_campaign_repo=campaign_repo,
            insight_repo=insight_repo,
        )

        synced = await use_case.execute(
            adapters={request.platform: (adapter, str(account_id))},
            organization_id=org_id,
        )

        return {
            "synced_count": len(synced),
            "platform": request.platform,
            "campaigns": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "status": c.status,
                    "sync_status": c.sync_status.value if hasattr(c.sync_status, "value") else str(c.sync_status),
                }
                for c in synced
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {e!s}",
        ) from e


@router.post(
    "/{account_id}/sync/{platform_campaign_id}",
    summary="Sync a single campaign from platform",
)
async def sync_single_campaign(
    account_id: UUID,
    platform_campaign_id: str,
    request: SyncSingleRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pull a single campaign's data from the platform."""
    try:
        from app.application.use_cases.campaigns.sync_use_cases import (
            SyncCampaignFromPlatformUseCase,
        )
        from app.infrastructure.db.repositories.campaigns.sync_repository import (
            AdCampaignRepoImpl,
            AdInsightRepoImpl,
        )
        from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found") from None
        org_id = user.organization_id

        await require_org_role(org_id, "member", user_id, db)

        adapter = _get_adapter(request.platform)
        campaign_repo = AdCampaignRepoImpl(db)
        insight_repo = AdInsightRepoImpl(db)

        use_case = SyncCampaignFromPlatformUseCase(
            ad_campaign_repo=campaign_repo,
            insight_repo=insight_repo,
        )

        ad_campaign = await use_case.execute(
            adapter=adapter,
            account_id=request.account_id or str(account_id),
            platform_campaign_id=platform_campaign_id,
            organization_id=org_id,
        )

        return {
            "id": str(ad_campaign.id),
            "name": ad_campaign.name,
            "status": ad_campaign.status,
            "sync_status": ad_campaign.sync_status.value if hasattr(ad_campaign.sync_status, "value") else str(ad_campaign.sync_status),
            "platform": ad_campaign.platform,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {e!s}",
        ) from e


@router.get(
    "/{account_id}/insights",
    summary="Refresh insights from ad platform",
)
async def refresh_insights(
    account_id: UUID,
    platform: str = Query("meta"),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pull latest insights from the platform for all active campaigns."""
    try:
        from app.application.use_cases.campaigns.sync_use_cases import (
            RefreshInsightsUseCase,
        )
        from app.infrastructure.db.repositories.campaigns.sync_repository import (
            AdInsightRepoImpl,
        )
        from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found") from None
        org_id = user.organization_id

        await require_org_role(org_id, "viewer", user_id, db)

        adapter = _get_adapter(platform)
        insight_repo = AdInsightRepoImpl(db)

        use_case = RefreshInsightsUseCase(insight_repo=insight_repo)
        insights = await use_case.execute(
            adapter=adapter,
            account_id=str(account_id),
            organization_id=org_id,
        )

        return {
            "insights_count": len(insights),
            "platform": platform,
            "insights": [
                {
                    "id": str(i.id),
                    "date": i.date,
                    "impressions": i.impressions,
                    "clicks": i.clicks,
                    "spend": i.spend,
                    "conversions": i.conversions,
                    "revenue": i.revenue,
                    "ctr": i.ctr,
                    "cpc": i.cpc,
                    "roas": i.roas,
                }
                for i in insights
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights refresh failed: {e!s}",
        ) from e
