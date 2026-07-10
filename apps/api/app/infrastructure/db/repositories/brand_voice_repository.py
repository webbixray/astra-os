from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.content.brand_voice import BrandVoice
from app.infrastructure.db.models.content.brand_voice_model import BrandVoiceModel


class BrandVoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, voice: BrandVoice) -> BrandVoice:
        model = BrandVoiceModel.from_domain(voice)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, voice_id: UUID) -> BrandVoice | None:
        result = await self.session.execute(
            select(BrandVoiceModel).where(BrandVoiceModel.id == voice_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID) -> list[BrandVoice]:
        result = await self.session.execute(
            select(BrandVoiceModel)
            .where(BrandVoiceModel.organization_id == org_id)
            .order_by(BrandVoiceModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, voice_id: UUID) -> None:
        result = await self.session.execute(
            select(BrandVoiceModel).where(BrandVoiceModel.id == voice_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
