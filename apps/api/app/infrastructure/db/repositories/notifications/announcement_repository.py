from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notifications.notification import BroadcastAnnouncement
from app.infrastructure.db.models.notifications.announcement_model import BroadcastAnnouncementModel


class AnnouncementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, announcement: BroadcastAnnouncement) -> BroadcastAnnouncement:
        model = BroadcastAnnouncementModel.from_domain(announcement)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_org(self, org_id: UUID) -> list[BroadcastAnnouncement]:
        result = await self.session.execute(
            select(BroadcastAnnouncementModel)
            .where(BroadcastAnnouncementModel.organization_id == org_id)
            .order_by(BroadcastAnnouncementModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_id(self, announcement_id: UUID) -> BroadcastAnnouncement | None:
        result = await self.session.execute(
            select(BroadcastAnnouncementModel).where(BroadcastAnnouncementModel.id == announcement_id)
        )
        m = result.scalar_one_or_none()
        return m.to_domain() if m else None

    async def add_dismissed(self, announcement_id: UUID, user_id: UUID) -> None:
        a = await self.session.get(BroadcastAnnouncementModel, announcement_id)
        if a:
            dismissed = list(a.dismissed_by or [])
            if user_id not in dismissed:
                dismissed.append(user_id)
                await self.session.execute(
                    update(BroadcastAnnouncementModel)
                    .where(BroadcastAnnouncementModel.id == announcement_id)
                    .values(dismissed_by=dismissed)
                )
                await self.session.flush()

    async def delete(self, announcement_id: UUID) -> None:
        m = await self.session.get(BroadcastAnnouncementModel, announcement_id)
        if m:
            await self.session.delete(m)
            await self.session.flush()
