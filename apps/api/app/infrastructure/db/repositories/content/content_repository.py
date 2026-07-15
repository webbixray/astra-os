from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.content.content_use_cases import ContentRepository
from app.domain.entities.content.content import Content
from app.infrastructure.db.models.content.content_model import ContentModel


class ContentRepositoryImpl(ContentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, content: Content) -> Content:
        model = ContentModel.from_domain(content)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, content_id: UUID) -> Content | None:
        result = await self.session.execute(
            select(ContentModel).where(ContentModel.id == content_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID, status: str | None = None) -> list[Content]:
        query = select(ContentModel).where(ContentModel.organization_id == org_id)
        if status is not None:
            query = query.where(ContentModel.status == status)
        query = query.order_by(ContentModel.created_at.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def find_by_campaign(self, campaign_id: UUID) -> list[Content]:
        result = await self.session.execute(
            select(ContentModel).where(ContentModel.campaign_id == campaign_id)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def delete(self, content_id: UUID) -> None:
        result = await self.session.execute(
            select(ContentModel).where(ContentModel.id == content_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()

    async def find_by_organization_and_date_range(
        self, org_id: UUID, start_date: datetime, end_date: datetime
    ) -> list[Content]:
        query = select(ContentModel).where(
            ContentModel.organization_id == org_id,
            ContentModel.created_at >= start_date,
            ContentModel.created_at <= end_date,
        )
        query = query.order_by(ContentModel.created_at.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]
