from datetime import UTC
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notifications.notification import Notification
from app.infrastructure.db.models.notifications.notification_model import NotificationModel


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, notification: Notification) -> Notification:
        model = NotificationModel.from_domain(notification)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        *,
        unread_only: bool = False,
        channel: str | None = None,
        archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        query = select(NotificationModel).where(
            NotificationModel.user_id == user_id,
            NotificationModel.organization_id == organization_id,
            NotificationModel.archived == archived,
        )
        if unread_only:
            query = query.where(NotificationModel.is_read.is_(False))
        if channel:
            query = query.where(NotificationModel.channel == channel)
        query = query.order_by(NotificationModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def count_by_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        *,
        unread_only: bool = False,
        channel: str | None = None,
        archived: bool = False,
    ) -> int:
        query = select(func.count()).where(
            NotificationModel.user_id == user_id,
            NotificationModel.organization_id == organization_id,
            NotificationModel.archived == archived,
        )
        if unread_only:
            query = query.where(NotificationModel.is_read.is_(False))
        if channel:
            query = query.where(NotificationModel.channel == channel)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_unread(
        self, user_id: UUID, organization_id: UUID, channel: str | None = None
    ) -> int:
        query = select(func.count()).where(
            NotificationModel.user_id == user_id,
            NotificationModel.organization_id == organization_id,
            NotificationModel.is_read.is_(False),
            NotificationModel.archived.is_(False),
        )
        if channel:
            query = query.where(NotificationModel.channel == channel)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_read(self, notification_id: UUID) -> None:
        from datetime import datetime

        await self.session.execute(
            update(NotificationModel)
            .where(NotificationModel.id == notification_id)
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        await self.session.flush()

    async def mark_all_read(self, user_id: UUID, organization_id: UUID) -> int:
        from datetime import datetime

        result = await self.session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.user_id == user_id,
                NotificationModel.organization_id == organization_id,
                NotificationModel.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        await self.session.flush()
        return result.rowcount

    async def archive(self, notification_id: UUID) -> None:
        await self.session.execute(
            update(NotificationModel)
            .where(NotificationModel.id == notification_id)
            .values(archived=True)
        )
        await self.session.flush()

    async def search(
        self,
        user_id: UUID,
        organization_id: UUID,
        query_str: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        query = select(NotificationModel).where(
            NotificationModel.user_id == user_id,
            NotificationModel.organization_id == organization_id,
        )
        query = query.where(
            NotificationModel.title.ilike(f"%{query_str}%")
            | NotificationModel.body.ilike(f"%{query_str}%")
        )
        query = query.order_by(NotificationModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]
