from uuid import UUID

from app.domain.entities.advertising.ad_campaign import AdCampaign, CampaignObjective
from app.infrastructure.db.repositories.advertising.advertising_repository import (
    AdCampaignRepository,
)
from app.infrastructure.external_adapters.adplatforms.base_adapter import (
    AdPlatformFactory,
)


class AdCampaignService:
    def __init__(self, repo: AdCampaignRepository):
        self.repo = repo

    async def create(
        self,
        organization_id: UUID,
        ad_account_id: UUID,
        name: str,
        objective: str = "awareness",
    ) -> dict:
        from app.infrastructure.db.models.advertising.advertising_models import AdCampaignModel

        campaign = AdCampaign.create(
            organization_id=organization_id,
            ad_account_id=ad_account_id,
            name=name,
            objective=CampaignObjective(objective),
        )

        model = AdCampaignModel(
            id=campaign.id,
            organization_id=organization_id,
            ad_account_id=ad_account_id,
            name=name,
            objective=objective,
        )
        saved = await self.repo.save(model)

        return {
            "id": str(saved.id),
            "name": saved.name,
            "objective": saved.objective,
            "status": saved.status,
        }

    async def list_by_organization(self, organization_id: UUID) -> list[dict]:
        models = await self.repo.find_by_organization(organization_id)
        return [
            {
                "id": str(m.id),
                "ad_account_id": str(m.ad_account_id),
                "name": m.name,
                "objective": m.objective,
                "status": m.status,
                "platform": m.platform,
                "sync_status": m.sync_status,
                "daily_budget": m.daily_budget,
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in models
        ]

    async def sync_to_platform(self, campaign_id: UUID) -> dict:
        model = await self.repo.find_by_id(campaign_id)
        if not model:
            return {"error": "Campaign not found"}

        adapter = AdPlatformFactory.create(
            __import__("app.domain.entities.advertising.ad_account", fromlist=["Platform"]).Platform(model.platform),
        )

        platform_id = await adapter.create_campaign(
            __import__("app.domain.entities.advertising.ad_campaign", fromlist=["AdCampaign"]).AdCampaign(
                name=model.name,
                platform=model.platform,
            )
        )

        model.platform_campaign_id = platform_id
        model.sync_status = "synced"
        await self.repo.save(model)

        return {"id": str(model.id), "platform_campaign_id": platform_id, "sync_status": "synced"}
