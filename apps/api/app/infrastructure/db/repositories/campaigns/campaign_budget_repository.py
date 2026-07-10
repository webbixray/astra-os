from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.campaigns.campaign_budget import CampaignBudget
from app.infrastructure.db.models.campaigns.campaign_budget_model import CampaignBudgetModel
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel


class CampaignBudgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, budget: CampaignBudget) -> CampaignBudget:
        model = CampaignBudgetModel.from_domain(budget)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_campaign(self, campaign_id: UUID) -> CampaignBudget | None:
        result = await self.session.execute(
            select(CampaignBudgetModel).where(CampaignBudgetModel.campaign_id == campaign_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_id(self, budget_id: UUID) -> CampaignBudget | None:
        result = await self.session.execute(
            select(CampaignBudgetModel).where(CampaignBudgetModel.id == budget_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_org(self, org_id: UUID) -> list[CampaignBudget]:
        result = await self.session.execute(
            select(CampaignBudgetModel)
            .join(CampaignModel, CampaignBudgetModel.campaign_id == CampaignModel.id)
            .where(CampaignModel.organization_id == org_id)
            .order_by(CampaignBudgetModel.updated_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]
