from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notifications.notification import NotificationTemplate
from app.infrastructure.db.models.notifications.notification_template_model import (
    NotificationTemplateModel,
)


class NotificationTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, template: NotificationTemplate) -> NotificationTemplate:
        model = NotificationTemplateModel.from_domain(template)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_org(self, org_id: UUID) -> list[NotificationTemplate]:
        result = await self.session.execute(
            select(NotificationTemplateModel)
            .where(NotificationTemplateModel.organization_id == org_id)
            .order_by(NotificationTemplateModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_id(self, template_id: UUID) -> NotificationTemplate | None:
        result = await self.session.execute(
            select(NotificationTemplateModel).where(NotificationTemplateModel.id == template_id)
        )
        m = result.scalar_one_or_none()
        return m.to_domain() if m else None

    async def delete(self, template_id: UUID) -> None:
        m = await self.session.get(NotificationTemplateModel, template_id)
        if m:
            await self.session.delete(m)
            await self.session.flush()
