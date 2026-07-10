from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.advertising.advertising_models import AdCampaignModel
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel


class BulkCampaignService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_status(
        self,
        organization_id: UUID,
        campaign_ids: list[UUID],
        status: str,
        scope: str = "campaign",
    ) -> dict:
        if scope == "ad":
            stmt = (
                update(AdCampaignModel)
                .where(
                    AdCampaignModel.organization_id == organization_id,
                    AdCampaignModel.id.in_(campaign_ids),
                )
                .values(status=status)
            )
        else:
            stmt = (
                update(CampaignModel)
                .where(
                    CampaignModel.organization_id == organization_id,
                    CampaignModel.id.in_(campaign_ids),
                )
                .values(status=status)
            )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return {
            "updated": result.rowcount,
            "status": status,
            "scope": scope,
        }

    async def get_overview(self, organization_id: UUID) -> dict:
        campaign_query = select(CampaignModel).where(
            CampaignModel.organization_id == organization_id,
        )
        campaign_result = await self.session.execute(campaign_query)
        campaigns = campaign_result.scalars().all()

        ad_query = select(AdCampaignModel).where(
            AdCampaignModel.organization_id == organization_id,
        )
        ad_result = await self.session.execute(ad_query)
        ad_campaigns = ad_result.scalars().all()

        campaign_statuses: dict[str, int] = {}
        for c in campaigns:
            campaign_statuses[c.status] = campaign_statuses.get(c.status, 0) + 1

        ad_statuses: dict[str, int] = {}
        for c in ad_campaigns:
            ad_statuses[c.status] = ad_statuses.get(c.status, 0) + 1

        platform_counts: dict[str, int] = {}
        for c in ad_campaigns:
            platform = c.platform or "unknown"
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        return {
            "total_campaigns": len(campaigns),
            "total_ad_campaigns": len(ad_campaigns),
            "campaign_status_breakdown": campaign_statuses,
            "ad_campaign_status_breakdown": ad_statuses,
            "ad_platform_breakdown": platform_counts,
            "combined_total": len(campaigns) + len(ad_campaigns),
        }
