from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.campaigns.ab_test import ABTest
from app.infrastructure.db.models.campaigns.ab_test_model import ABTestModel, ABTestVariantModel


class ABTestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, test: ABTest) -> ABTest:
        model = ABTestModel.from_domain(test)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, test_id: UUID) -> ABTest | None:
        result = await self.session.execute(select(ABTestModel).where(ABTestModel.id == test_id))
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_campaign(self, campaign_id: UUID) -> list[ABTest]:
        result = await self.session.execute(
            select(ABTestModel)
            .where(ABTestModel.campaign_id == campaign_id)
            .order_by(ABTestModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_organization(self, org_id: UUID) -> list[ABTest]:
        result = await self.session.execute(
            select(ABTestModel)
            .where(ABTestModel.organization_id == org_id)
            .order_by(ABTestModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_with_variants(self, test_id: UUID) -> ABTest | None:
        test = await self.find_by_id(test_id)
        if test is None:
            return None
        test.variants = await self.find_variants(test_id)
        return test

    async def save_variant(self, variant) -> None:
        model = ABTestVariantModel.from_domain(variant)
        await self.session.merge(model)
        await self.session.flush()

    async def find_variants(self, test_id: UUID) -> list:
        result = await self.session.execute(
            select(ABTestVariantModel).where(ABTestVariantModel.ab_test_id == test_id)
        )
        return [m.to_domain() for m in result.scalars().all()]
