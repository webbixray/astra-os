from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.email.email_campaign import EmailCampaign
from app.infrastructure.db.models.email.email_campaign_model import EmailCampaignModel


class EmailCampaignRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, campaign: EmailCampaign) -> EmailCampaign:
        model = EmailCampaignModel.from_domain(campaign)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, campaign_id: UUID) -> EmailCampaign | None:
        result = await self.session.execute(
            select(EmailCampaignModel).where(EmailCampaignModel.id == campaign_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(
        self, org_id: UUID, status: str | None = None
    ) -> list[EmailCampaign]:
        query = select(EmailCampaignModel).where(EmailCampaignModel.organization_id == org_id)
        if status is not None:
            query = query.where(EmailCampaignModel.status == status)
        query = query.order_by(EmailCampaignModel.created_at.desc())
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def get_analytics(self, org_id: UUID) -> dict:
        campaigns = await self.find_by_organization(org_id)
        total = len(campaigns)
        total_sent = sum(c.sent_count for c in campaigns)
        total_opens = sum(c.open_count for c in campaigns)
        total_clicks = sum(c.click_count for c in campaigns)
        total_bounces = sum(c.bounce_count for c in campaigns)
        return {
            "total_campaigns": total,
            "total_sent": total_sent,
            "total_opens": total_opens,
            "total_clicks": total_clicks,
            "total_bounces": total_bounces,
            "avg_open_rate": (total_opens / total_sent * 100) if total_sent > 0 else 0.0,
            "avg_click_rate": (total_clicks / total_sent * 100) if total_sent > 0 else 0.0,
            "avg_bounce_rate": (total_bounces / total_sent * 100) if total_sent > 0 else 0.0,
        }

    async def delete(self, campaign_id: UUID) -> None:
        result = await self.session.execute(
            select(EmailCampaignModel).where(EmailCampaignModel.id == campaign_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
