from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import OrganizationRepository
from app.domain.entities.organization import Organization
from app.infrastructure.db.models.organization import OrganizationModel


class OrganizationRepositoryImpl(OrganizationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, org: Organization) -> Organization:
        model = OrganizationModel.from_domain(org)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, org_id: UUID) -> Organization | None:
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == org_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_parent(self, parent_org_id: UUID) -> list[Organization]:
        result = await self.session.execute(
            select(OrganizationModel)
            .where(OrganizationModel.parent_org_id == parent_org_id)
            .order_by(OrganizationModel.name)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_ids(self, ids: list[UUID]) -> list[Organization]:
        if not ids:
            return []
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id.in_(ids))
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, org_id: UUID) -> None:
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == org_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
