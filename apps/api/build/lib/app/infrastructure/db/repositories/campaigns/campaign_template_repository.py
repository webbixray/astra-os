from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.campaigns.campaign_template import CampaignTemplate
from app.infrastructure.db.models.campaigns.campaign_template_model import CampaignTemplateModel


class CampaignTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, template: CampaignTemplate) -> CampaignTemplate:
        model = CampaignTemplateModel.from_domain(template)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, template_id: UUID) -> CampaignTemplate | None:
        result = await self.session.execute(
            select(CampaignTemplateModel).where(CampaignTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID) -> list[CampaignTemplate]:
        result = await self.session.execute(
            select(CampaignTemplateModel)
            .where(CampaignTemplateModel.organization_id == org_id)
            .order_by(CampaignTemplateModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, template_id: UUID) -> None:
        result = await self.session.execute(
            select(CampaignTemplateModel).where(CampaignTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
