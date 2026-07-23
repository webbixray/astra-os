from datetime import UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.content.content_publish import ContentPublish
from app.infrastructure.db.models.content.content_publish_model import ContentPublishModel


class ContentPublishRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, publish: ContentPublish) -> ContentPublish:
        model = ContentPublishModel.from_domain(publish)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, publish_id: UUID) -> ContentPublish | None:
        result = await self.session.execute(
            select(ContentPublishModel).where(ContentPublishModel.id == publish_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_content(self, content_id: UUID) -> list[ContentPublish]:
        result = await self.session.execute(
            select(ContentPublishModel)
            .where(ContentPublishModel.content_id == content_id)
            .order_by(ContentPublishModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_queue_by_org(
        self, org_id: UUID, status: str | None = None
    ) -> list[ContentPublish]:
        from app.infrastructure.db.models.content.content_model import ContentModel

        query = (
            select(ContentPublishModel)
            .join(ContentModel, ContentPublishModel.content_id == ContentModel.id)
            .where(ContentModel.organization_id == org_id)
        )
        if status is not None:
            query = query.where(ContentPublishModel.status == status)
        query = query.order_by(
            ContentPublishModel.scheduled_at.asc().nullslast(),
            ContentPublishModel.created_at.desc(),
        )
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def find_scheduled_due(self) -> list[ContentPublish]:
        from datetime import datetime

        result = await self.session.execute(
            select(ContentPublishModel)
            .where(
                ContentPublishModel.status == "scheduled",
                ContentPublishModel.scheduled_at <= datetime.now(UTC),
            )
            .order_by(ContentPublishModel.scheduled_at.asc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, publish_id: UUID) -> None:
        result = await self.session.execute(
            select(ContentPublishModel).where(ContentPublishModel.id == publish_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
