from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.email.email_event import EmailEvent
from app.infrastructure.db.models.email.email_event_model import EmailEventModel


class EmailEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: EmailEvent) -> EmailEvent:
        model = EmailEventModel.from_domain(event)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def save_all(self, events: list[EmailEvent]) -> list[EmailEvent]:
        models = [EmailEventModel.from_domain(e) for e in events]
        self.session.add_all(models)
        await self.session.flush()
        return [m.to_domain() for m in models]

    async def find_by_campaign(
        self, campaign_id: UUID, event_type: str | None = None
    ) -> list[EmailEvent]:
        query = select(EmailEventModel).where(EmailEventModel.campaign_id == campaign_id)
        if event_type is not None:
            query = query.where(EmailEventModel.event_type == event_type)
        query = query.order_by(EmailEventModel.occurred_at.desc())
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def count_by_type(self, campaign_id: UUID) -> dict[str, int]:
        result = await self.session.execute(
            select(EmailEventModel.event_type, func.count())
            .where(EmailEventModel.campaign_id == campaign_id)
            .group_by(EmailEventModel.event_type)
        )
        return {row[0]: row[1] for row in result.all()}
