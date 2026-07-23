from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.campaign_use_cases import CampaignRepository
from app.domain.entities.campaigns.campaign import Campaign
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel


class CampaignRepositoryImpl(CampaignRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, campaign: Campaign) -> Campaign:
        model = CampaignModel.from_domain(campaign)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, campaign_id: UUID) -> Campaign | None:
        result = await self.session.execute(
            select(CampaignModel).where(CampaignModel.id == campaign_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID, status: str | None = None) -> list[Campaign]:
        query = select(CampaignModel).where(CampaignModel.organization_id == org_id)
        if status is not None:
            query = query.where(CampaignModel.status == status)
        query = query.order_by(CampaignModel.created_at.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def delete(self, campaign_id: UUID) -> None:
        result = await self.session.execute(
            select(CampaignModel).where(CampaignModel.id == campaign_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()

    async def find_by_organization_and_date_range(
        self, org_id: UUID, start_date: datetime, end_date: datetime
    ) -> list[Campaign]:
        query = select(CampaignModel).where(
            CampaignModel.organization_id == org_id,
            CampaignModel.created_at >= start_date,
            CampaignModel.created_at <= end_date,
        )
        query = query.order_by(CampaignModel.created_at.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]
