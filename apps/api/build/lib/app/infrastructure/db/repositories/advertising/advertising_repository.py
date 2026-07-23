from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.advertising.advertising_models import (
    AdAccountModel,
    AdCampaignModel,
    AdCreativeModel,
)


class AdAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, model: AdAccountModel) -> AdAccountModel:
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def find_by_id(self, id: UUID) -> AdAccountModel | None:
        result = await self.db.execute(select(AdAccountModel).where(AdAccountModel.id == id))
        return result.scalar_one_or_none()

    async def find_by_organization(self, org_id: UUID) -> list[AdAccountModel]:
        result = await self.db.execute(
            select(AdAccountModel)
            .where(AdAccountModel.organization_id == org_id)
            .order_by(AdAccountModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, id: UUID) -> None:
        await self.db.execute(delete(AdAccountModel).where(AdAccountModel.id == id))
        await self.db.commit()


class AdCampaignRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, model: AdCampaignModel) -> AdCampaignModel:
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def find_by_id(self, id: UUID) -> AdCampaignModel | None:
        result = await self.db.execute(select(AdCampaignModel).where(AdCampaignModel.id == id))
        return result.scalar_one_or_none()

    async def find_by_organization(self, org_id: UUID) -> list[AdCampaignModel]:
        result = await self.db.execute(
            select(AdCampaignModel)
            .where(AdCampaignModel.organization_id == org_id)
            .order_by(AdCampaignModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_by_account(self, account_id: UUID) -> list[AdCampaignModel]:
        result = await self.db.execute(
            select(AdCampaignModel)
            .where(AdCampaignModel.ad_account_id == account_id)
            .order_by(AdCampaignModel.created_at.desc())
        )
        return list(result.scalars().all())


class AdCreativeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, model: AdCreativeModel) -> AdCreativeModel:
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def find_by_id(self, id: UUID) -> AdCreativeModel | None:
        result = await self.db.execute(select(AdCreativeModel).where(AdCreativeModel.id == id))
        return result.scalar_one_or_none()

    async def find_by_organization(self, org_id: UUID) -> list[AdCreativeModel]:
        result = await self.db.execute(
            select(AdCreativeModel)
            .where(AdCreativeModel.organization_id == org_id)
            .order_by(AdCreativeModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_by_campaign(self, campaign_id: UUID) -> list[AdCreativeModel]:
        result = await self.db.execute(
            select(AdCreativeModel).where(AdCreativeModel.ad_campaign_id == campaign_id)
        )
        return list(result.scalars().all())
