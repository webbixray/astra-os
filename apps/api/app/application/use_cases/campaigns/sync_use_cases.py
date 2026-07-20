"""Campaign Sync Service — pulls performance data from ad platforms.

Bridges external ad platform adapters (Meta, Google, LinkedIn, TikTok)
with the internal Campaign and AdInsight entities. Handles syncing
campaign status, pulling insights, and updating local state.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.common import now
from app.domain.entities.advertising.ad_campaign import AdCampaign, SyncStatus
from app.domain.entities.advertising.ad_insights import AdInsight
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus

if TYPE_CHECKING:
    from app.application.ports.ad_platform_port import AdPlatformPort

logger = logging.getLogger(__name__)


class AdInsightRepository:
    async def save(self, insight: AdInsight) -> AdInsight: ...
    async def find_by_campaign(self, campaign_id: UUID) -> list[AdInsight]: ...
    async def find_by_date_range(
        self, campaign_id: UUID, start: str, end: str
    ) -> list[AdInsight]: ...


class AdCampaignRepository:
    async def save(self, ad_campaign: AdCampaign) -> AdCampaign: ...
    async def find_by_platform_campaign_id(
        self, platform_campaign_id: str, platform: str
    ) -> AdCampaign | None: ...
    async def find_by_organization(self, org_id: UUID) -> list[AdCampaign]: ...


class SyncCampaignFromPlatformUseCase:
    """Pull campaign data from an ad platform and update local state.

    This is called per-campaign to sync its status, budget, and basic
    performance metrics from the platform API.
    """

    def __init__(
        self,
        ad_campaign_repo: AdCampaignRepository,
        insight_repo: AdInsightRepository,
    ):
        self.ad_campaign_repo = ad_campaign_repo
        self.insight_repo = insight_repo

    async def execute(
        self,
        adapter: AdPlatformPort,
        account_id: str,
        platform_campaign_id: str,
        organization_id: UUID,
    ) -> AdCampaign:
        """Sync a single campaign from the platform.

        Args:
            adapter: The platform adapter (Meta, Google, etc.)
            account_id: The platform account ID.
            platform_campaign_id: The campaign ID on the platform.
            organization_id: Our internal organization UUID.

        Returns:
            The updated AdCampaign entity.

        """
        # Fetch performance data from platform
        campaigns = await adapter.get_performance(account_id, [platform_campaign_id])

        if not campaigns:
            logger.warning(
                "No data returned from %s for campaign %s",
                adapter.platform.value,
                platform_campaign_id,
            )
            # Return existing or create placeholder
            existing = await self.ad_campaign_repo.find_by_platform_campaign_id(
                platform_campaign_id, adapter.platform.value
            )
            if existing:
                return existing
            # Create a stub
            ad_campaign = AdCampaign(
                organization_id=organization_id,
                ad_account_id=UUID(),
                name=f"Synced from {adapter.platform.value}",
                platform=adapter.platform.value,
                platform_campaign_id=platform_campaign_id,
                sync_status=SyncStatus.FAILED,
            )
            return await self.ad_campaign_repo.save(ad_campaign)

        platform_campaign = campaigns[0]

        # Check if we already have this campaign locally
        existing = await self.ad_campaign_repo.find_by_platform_campaign_id(
            platform_campaign_id, adapter.platform.value
        )

        if existing:
            # Update existing
            existing.status = platform_campaign.status.value
            existing.daily_budget = platform_campaign.budget
            existing.lifetime_budget = platform_campaign.budget
            existing.sync_status = SyncStatus.SYNCED
            existing.updated_at = now()
            ad_campaign = await self.ad_campaign_repo.save(existing)
        else:
            # Create new
            ad_campaign = AdCampaign(
                organization_id=organization_id,
                ad_account_id=UUID(),
                name=platform_campaign.name,
                objective=platform_campaign.objective
                if hasattr(platform_campaign, "objective")
                else None,
                status=platform_campaign.status.value,
                platform=adapter.platform.value,
                platform_campaign_id=platform_campaign_id,
                daily_budget=platform_campaign.budget,
                lifetime_budget=platform_campaign.budget,
                currency=platform_campaign.currency,
                sync_status=SyncStatus.SYNCED,
                start_date=platform_campaign.start_date,
                end_date=platform_campaign.end_date,
            )
            ad_campaign = await self.ad_campaign_repo.save(ad_campaign)

        # Store insight data
        if platform_campaign.impressions > 0 or platform_campaign.clicks > 0:
            insight = AdInsight(
                organization_id=organization_id,
                ad_campaign_id=ad_campaign.id,
                date=date.today().isoformat(),
                impressions=platform_campaign.impressions,
                clicks=platform_campaign.clicks,
                spend=platform_campaign.spend,
                conversions=platform_campaign.conversions,
                revenue=platform_campaign.revenue,
                platform=adapter.platform.value,
            )
            await self.insight_repo.save(insight)

        # Publish sync event
        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.AD_CAMPAIGN_SYNCED,
                aggregate_id=str(ad_campaign.id),
                aggregate_type="ad_campaign",
                data={
                    "organization_id": str(organization_id),
                    "platform": adapter.platform.value,
                    "platform_campaign_id": platform_campaign_id,
                    "status": ad_campaign.status,
                    "sync_status": ad_campaign.sync_status.value,
                },
            )
        )

        logger.info(
            "Synced campaign %s from %s: status=%s, spend=$%.2f",
            platform_campaign_id,
            adapter.platform.value,
            ad_campaign.status,
            platform_campaign.spend,
        )

        return ad_campaign


class SyncAllCampaignsUseCase:
    """Sync all campaigns for an organization across all connected platforms."""

    def __init__(
        self,
        ad_campaign_repo: AdCampaignRepository,
        insight_repo: AdInsightRepository,
    ):
        self.ad_campaign_repo = ad_campaign_repo
        self.insight_repo = insight_repo
        self._sync_single = SyncCampaignFromPlatformUseCase(ad_campaign_repo, insight_repo)

    async def execute(
        self,
        adapters: dict[str, tuple[AdPlatformPort, str]],
        organization_id: UUID,
    ) -> list[AdCampaign]:
        """Sync all campaigns across all connected platforms.

        Args:
            adapters: Dict of platform_name → (adapter, account_id)
            organization_id: Our internal organization UUID.

        Returns:
            List of synced AdCampaign entities.

        """
        synced: list[AdCampaign] = []

        for platform_name, (adapter, account_id) in adapters.items():
            try:
                campaigns = await adapter.get_campaigns(account_id)
                for platform_campaign in campaigns:
                    try:
                        ad_campaign = await self._sync_single.execute(
                            adapter=adapter,
                            account_id=account_id,
                            platform_campaign_id=platform_campaign.id,
                            organization_id=organization_id,
                        )
                        synced.append(ad_campaign)
                    except Exception:
                        logger.exception(
                            "Failed to sync campaign %s from %s",
                            platform_campaign.id,
                            platform_name,
                        )
            except Exception:
                logger.exception("Failed to fetch campaigns from %s", platform_name)

        logger.info(
            "Synced %d campaigns for org %s across %d platforms",
            len(synced),
            organization_id,
            len(adapters),
        )

        return synced


class RefreshInsightsUseCase:
    """Pull latest insights for all active ad campaigns of an organization."""

    def __init__(self, insight_repo: AdInsightRepository):
        self.insight_repo = insight_repo

    async def execute(
        self,
        adapter: AdPlatformPort,
        account_id: str,
        organization_id: UUID,
        ad_campaign_id: UUID | None = None,
    ) -> list[AdInsight]:
        """Refresh insights from the platform.

        Args:
            adapter: The platform adapter.
            account_id: Platform account ID.
            organization_id: Our org UUID.
            ad_campaign_id: Optional — limit to a single campaign.

        Returns:
            List of refreshed AdInsight entities.

        """
        campaigns = await adapter.get_performance(account_id)

        insights: list[AdInsight] = []
        for c in campaigns:
            insight = AdInsight(
                organization_id=organization_id,
                ad_campaign_id=ad_campaign_id,
                date=date.today().isoformat(),
                impressions=c.impressions,
                clicks=c.clicks,
                spend=c.spend,
                conversions=c.conversions,
                revenue=c.revenue,
                platform=adapter.platform.value,
            )
            saved = await self.insight_repo.save(insight)
            insights.append(saved)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.AD_INSIGHTS_REFRESHED,
                aggregate_id=account_id,
                aggregate_type="ad_account",
                data={
                    "organization_id": str(organization_id),
                    "platform": adapter.platform.value,
                    "insights_count": len(insights),
                },
            )
        )

        logger.info(
            "Refreshed %d insights from %s for account %s",
            len(insights),
            adapter.platform.value,
            account_id,
        )

        return insights
