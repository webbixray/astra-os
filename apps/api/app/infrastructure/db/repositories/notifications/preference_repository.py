from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notifications.notification import UserNotificationPreference
from app.infrastructure.db.models.notifications.preference_model import (
    UserNotificationPreferenceModel,
)


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, pref: UserNotificationPreference) -> UserNotificationPreference:
        model = UserNotificationPreferenceModel.from_domain(pref)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_user(self, user_id: UUID) -> list[UserNotificationPreference]:
        result = await self.session.execute(
            select(UserNotificationPreferenceModel)
            .where(UserNotificationPreferenceModel.user_id == user_id)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_user_and_type(self, user_id: UUID, notification_type: str, channel: str) -> UserNotificationPreference | None:
        result = await self.session.execute(
            select(UserNotificationPreferenceModel).where(
                UserNotificationPreferenceModel.user_id == user_id,
                UserNotificationPreferenceModel.notification_type == notification_type,
                UserNotificationPreferenceModel.channel == channel,
            )
        )
        m = result.scalar_one_or_none()
        return m.to_domain() if m else None

    async def upsert(self, pref: UserNotificationPreference) -> UserNotificationPreference:
        existing = await self.find_by_user_and_type(pref.user_id, pref.notification_type, pref.channel)
        if existing:
            await self.session.execute(
                update(UserNotificationPreferenceModel)
                .where(UserNotificationPreferenceModel.id == existing.id)
                .values(enabled=pref.enabled, updated_at=pref.updated_at)
            )
            await self.session.flush()
            existing.enabled = pref.enabled
            return existing
        return await self.save(pref)
