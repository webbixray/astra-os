"""Sync Repositories — SQLAlchemy implementations for ad campaign + insight sync.

Provides two repositories matching the port interfaces in sync_use_cases.py:
- AdCampaignRepoImpl (implements AdCampaignRepository)
- AdInsightRepoImpl (implements AdInsightRepository)
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.sync_use_cases import (
    AdCampaignRepository,
    AdInsightRepository,
)
from app.domain.entities.advertising.ad_campaign import AdCampaign, SyncStatus
from app.domain.entities.advertising.ad_insights import AdInsight
from app.infrastructure.db.models.advertising.advertising_models import (
    AdCampaignModel,
    AdInsightModel,
)


class AdCampaignRepoImpl(AdCampaignRepository):
    """Implements AdCampaignRepository port for sync operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ad_campaign: AdCampaign) -> AdCampaign:
        model = AdCampaignModel(
            id=ad_campaign.id,
            organization_id=ad_campaign.organization_id,
            ad_account_id=ad_campaign.ad_account_id,
            name=ad_campaign.name,
            objective=ad_campaign.objective.value
            if hasattr(ad_campaign.objective, "value")
            else (ad_campaign.objective or "awareness"),
            status=ad_campaign.status,
            platform_campaign_id=ad_campaign.platform_campaign_id,
            platform=ad_campaign.platform,
            daily_budget=ad_campaign.daily_budget,
            lifetime_budget=ad_campaign.lifetime_budget,
            currency=ad_campaign.currency,
            start_date=ad_campaign.start_date,
            end_date=ad_campaign.end_date,
            targeting=ad_campaign.targeting,
            creatives=ad_campaign.creatives,
            sync_status=ad_campaign.sync_status.value
            if hasattr(ad_campaign.sync_status, "value")
            else str(ad_campaign.sync_status),
            created_by=ad_campaign.created_by,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return _model_to_domain(merged)

    async def find_by_platform_campaign_id(
        self, platform_campaign_id: str, platform: str
    ) -> AdCampaign | None:
        result = await self.session.execute(
            select(AdCampaignModel).where(
                AdCampaignModel.platform_campaign_id == platform_campaign_id,
                AdCampaignModel.platform == platform,
            )
        )
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    async def find_by_organization(self, org_id: UUID) -> list[AdCampaign]:
        result = await self.session.execute(
            select(AdCampaignModel)
            .where(AdCampaignModel.organization_id == org_id)
            .order_by(AdCampaignModel.created_at.desc())
        )
        return [_model_to_domain(m) for m in result.scalars().all()]


class AdInsightRepoImpl(AdInsightRepository):
    """Implements AdInsightRepository port for sync operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, insight: AdInsight) -> AdInsight:
        model = AdInsightModel(
            id=insight.id,
            organization_id=insight.organization_id,
            ad_campaign_id=insight.ad_campaign_id,
            date=insight.date,
            impressions=insight.impressions,
            clicks=insight.clicks,
            spend=insight.spend,
            conversions=insight.conversions,
            revenue=insight.revenue,
            platform=insight.platform,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return _insight_to_domain(merged)

    async def find_by_campaign(self, campaign_id: UUID) -> list[AdInsight]:
        result = await self.session.execute(
            select(AdInsightModel)
            .where(AdInsightModel.ad_campaign_id == campaign_id)
            .order_by(AdInsightModel.date.desc())
        )
        return [_insight_to_domain(m) for m in result.scalars().all()]

    async def find_by_date_range(self, campaign_id: UUID, start: str, end: str) -> list[AdInsight]:
        result = await self.session.execute(
            select(AdInsightModel)
            .where(
                AdInsightModel.ad_campaign_id == campaign_id,
                AdInsightModel.date >= start,
                AdInsightModel.date <= end,
            )
            .order_by(AdInsightModel.date.desc())
        )
        return [_insight_to_domain(m) for m in result.scalars().all()]


# ── Mapping helpers ──────────────────────────────────────────────────


def _model_to_domain(model: AdCampaignModel) -> AdCampaign:
    return AdCampaign(
        id=model.id,
        organization_id=model.organization_id,
        ad_account_id=model.ad_account_id,
        name=model.name,
        status=model.status,
        platform_campaign_id=model.platform_campaign_id or "",
        platform=model.platform or "",
        daily_budget=model.daily_budget or 0,
        lifetime_budget=model.lifetime_budget or 0,
        currency=model.currency or "USD",
        start_date=model.start_date or "",
        end_date=model.end_date or "",
        targeting=model.targeting or {},
        creatives=model.creatives or [],
        sync_status=SyncStatus(model.sync_status) if model.sync_status else SyncStatus.NOT_SYNCED,
        created_by=model.created_by,
    )


def _insight_to_domain(model: AdInsightModel) -> AdInsight:
    return AdInsight(
        id=model.id,
        organization_id=model.organization_id,
        ad_campaign_id=model.ad_campaign_id,
        date=model.date or "",
        impressions=model.impressions or 0,
        clicks=model.clicks or 0,
        spend=model.spend or 0,
        conversions=model.conversions or 0,
        revenue=model.revenue or 0,
        platform=model.platform or "",
    )
