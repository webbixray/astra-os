"""Creative Repository — SQLAlchemy implementation of CreativeRepository port."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.creative_use_cases import CreativeRepository
from app.domain.entities.advertising.ad_creative import AdCreative, CreativeStatus
from app.infrastructure.db.models.advertising.advertising_models import AdCreativeModel


class CreativeRepositoryImpl(CreativeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, creative: AdCreative) -> AdCreative:
        model = AdCreativeModel.from_domain(creative)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, creative_id: UUID) -> AdCreative | None:
        result = await self.session.execute(
            select(AdCreativeModel).where(AdCreativeModel.id == creative_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(
        self, org_id: UUID, status: CreativeStatus | None = None
    ) -> list[AdCreative]:
        query = select(AdCreativeModel).where(AdCreativeModel.organization_id == org_id)
        if status is not None:
            query = query.where(AdCreativeModel.status == status.value)
        query = query.order_by(AdCreativeModel.created_at.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def find_by_campaign(self, campaign_id: UUID) -> list[AdCreative]:
        query = (
            select(AdCreativeModel)
            .where(AdCreativeModel.ad_campaign_id == campaign_id)
            .order_by(AdCreativeModel.created_at.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def delete(self, creative_id: UUID) -> None:
        result = await self.session.execute(
            select(AdCreativeModel).where(AdCreativeModel.id == creative_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
