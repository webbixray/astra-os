from datetime import date as dt_date
from uuid import UUID

from sqlalchemy import Date, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.advertising.advertising_models import AdCampaignModel
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.content.content_model import ContentModel


class CalendarEvent:
    def __init__(
        self,
        id: str,
        type: str,
        title: str,
        start_date: str | None,
        end_date: str | None,
        status: str,
        link: str | None = None,
    ):
        self.id = id
        self.type = type
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.link = link

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "link": self.link,
        }


class CalendarService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events(
        self,
        organization_id: UUID,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        start = dt_date.fromisoformat(start_date)
        end = dt_date.fromisoformat(end_date)

        events: list[CalendarEvent] = []

        campaign_events = await self._get_campaign_events(organization_id, start, end)
        content_events = await self._get_content_events(organization_id, start, end)
        ad_events = await self._get_ad_events(organization_id, start, end)

        events.extend(campaign_events)
        events.extend(content_events)
        events.extend(ad_events)

        events.sort(key=lambda e: e.start_date or "")

        return [e.to_dict() for e in events]

    async def _get_campaign_events(
        self, organization_id: UUID, start: dt_date, end: dt_date
    ) -> list[CalendarEvent]:
        query = select(CampaignModel).where(
            CampaignModel.organization_id == organization_id,
            or_(
                CampaignModel.start_date.between(start, end),
                CampaignModel.end_date.between(start, end),
                CampaignModel.created_at.cast(Date).between(start, end),
            ),
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [
            CalendarEvent(
                id=str(m.id),
                type="campaign",
                title=m.name,
                start_date=m.start_date.isoformat() if m.start_date else None,
                end_date=m.end_date.isoformat() if m.end_date else None,
                status=m.status,
                link=f"/campaigns/{m.id}",
            )
            for m in models
        ]

    async def _get_content_events(
        self, organization_id: UUID, start: dt_date, end: dt_date
    ) -> list[CalendarEvent]:
        query = select(ContentModel).where(
            ContentModel.organization_id == organization_id,
            or_(
                ContentModel.scheduled_at.cast(Date).between(start, end),
                ContentModel.published_at.cast(Date).between(start, end),
            ),
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [
            CalendarEvent(
                id=str(m.id),
                type="content",
                title=m.title,
                start_date=m.scheduled_at.isoformat() if m.scheduled_at else (m.published_at.isoformat() if m.published_at else None),
                end_date=None,
                status=m.status,
                link=f"/content/{m.id}",
            )
            for m in models
        ]

    async def _get_ad_events(
        self, organization_id: UUID, start: dt_date, end: dt_date
    ) -> list[CalendarEvent]:
        query = select(AdCampaignModel).where(
            AdCampaignModel.organization_id == organization_id,
            or_(
                AdCampaignModel.start_date.between(start.isoformat(), end.isoformat()),
                AdCampaignModel.end_date.between(start.isoformat(), end.isoformat()),
            ),
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [
            CalendarEvent(
                id=str(m.id),
                type="ad_campaign",
                title=m.name,
                start_date=m.start_date,
                end_date=m.end_date,
                status=m.status,
                link=f"/advertising/{m.ad_account_id}",
            )
            for m in models
        ]
