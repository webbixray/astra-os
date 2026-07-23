import logging
from uuid import UUID

from app.domain.entities.email.email_campaign import EmailCampaign
from app.domain.entities.email.email_event import EmailEvent
from app.domain.entities.email.email_provider import EmailProvider
from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.domain.services.email.senders import get_sender

logger = logging.getLogger(__name__)


class EmailProviderRepository:
    async def save(self, provider: EmailProvider) -> EmailProvider: ...
    async def find_by_id(self, provider_id: UUID) -> EmailProvider | None: ...
    async def find_by_organization(self, org_id: UUID) -> list[EmailProvider]: ...
    async def find_active(self, org_id: UUID) -> EmailProvider | None: ...
    async def delete(self, provider_id: UUID) -> None: ...


class EmailCampaignRepository:
    async def save(self, campaign: EmailCampaign) -> EmailCampaign: ...
    async def find_by_id(self, campaign_id: UUID) -> EmailCampaign | None: ...
    async def find_by_organization(
        self, org_id: UUID, status: str | None = None
    ) -> list[EmailCampaign]: ...
    async def get_analytics(self, org_id: UUID) -> dict: ...
    async def delete(self, campaign_id: UUID) -> None: ...


class EmailEventRepository:
    async def save(self, event: EmailEvent) -> EmailEvent: ...
    async def find_by_campaign(
        self, campaign_id: UUID, event_type: str | None = None
    ) -> list[EmailEvent]: ...
    async def count_by_type(self, campaign_id: UUID) -> dict[str, int]: ...


class EmailService:
    def __init__(
        self,
        provider_repo: EmailProviderRepository,
        campaign_repo: EmailCampaignRepository,
        event_repo: EmailEventRepository,
    ):
        self.provider_repo = provider_repo
        self.campaign_repo = campaign_repo
        self.event_repo = event_repo

    # ── Provider management ────────────────────────────────────────────────

    async def create_provider(
        self,
        org_id: UUID,
        provider_type: str,
        name: str,
        api_key: str,
        from_email: str,
        created_by: UUID,
        from_name: str = "",
        config: dict | None = None,
    ) -> EmailProvider:
        provider = EmailProvider.create(
            organization_id=org_id,
            provider_type=provider_type,
            name=name,
            api_key=api_key,
            from_email=from_email,
            created_by=created_by,
            from_name=from_name,
            config=config,
        )
        return await self.provider_repo.save(provider)

    async def list_providers(self, org_id: UUID) -> list[EmailProvider]:
        return await self.provider_repo.find_by_organization(org_id)

    async def delete_provider(self, provider_id: UUID) -> None:
        await self.provider_repo.delete(provider_id)

    # ── Campaign management ────────────────────────────────────────────────

    async def create_campaign(
        self,
        org_id: UUID,
        provider_id: UUID,
        name: str,
        subject: str,
        body: str,
        from_email: str,
        created_by: UUID,
        from_name: str = "",
        scheduled_at: str | None = None,
    ) -> EmailCampaign:
        from datetime import datetime as dt

        parsed = dt.fromisoformat(scheduled_at) if scheduled_at else None
        campaign = EmailCampaign.create(
            organization_id=org_id,
            provider_id=provider_id,
            name=name,
            subject=subject,
            body=body,
            from_email=from_email,
            created_by=created_by,
            from_name=from_name,
            scheduled_at=parsed,
        )
        return await self.campaign_repo.save(campaign)

    async def list_campaigns(self, org_id: UUID, status: str | None = None) -> list[EmailCampaign]:
        return await self.campaign_repo.find_by_organization(org_id, status=status)

    async def get_campaign(self, campaign_id: UUID) -> EmailCampaign:
        campaign = await self.campaign_repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("EmailCampaign", str(campaign_id))
        return campaign

    async def send_campaign(self, campaign_id: UUID, recipients: list[str]) -> EmailCampaign:
        campaign = await self.campaign_repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("EmailCampaign", str(campaign_id))
        campaign.send()
        await self.campaign_repo.save(campaign)

        provider = await self.provider_repo.find_by_id(campaign.provider_id)
        if provider is None:
            campaign.fail()
            return await self.campaign_repo.save(campaign)

        sender = get_sender(provider.provider_type)
        if sender is None:
            campaign.fail()
            return await self.campaign_repo.save(campaign)

        try:
            result = await sender.send(
                to=recipients,
                subject=campaign.subject,
                body=campaign.body,
                from_email=campaign.from_email,
                from_name=campaign.from_name,
                metadata={"campaign_id": str(campaign.id)},
            )
            campaign.complete(sent=result.get("sent_count", len(recipients)))
            saved = await self.campaign_repo.save(campaign)

            events = [
                EmailEvent.create(
                    campaign_id=campaign.id,
                    event_type="sent",
                    recipient_email=recipient,
                )
                for recipient in recipients
            ]
            await self.event_repo.save_all(events)
        except Exception:
            logger.exception("Email campaign %s failed to send", campaign.id)
            campaign.fail()
            return await self.campaign_repo.save(campaign)
        else:
            return saved

    async def get_analytics(self, org_id: UUID) -> dict:
        return await self.campaign_repo.get_analytics(org_id)

    async def get_campaign_events(
        self, campaign_id: UUID, event_type: str | None = None
    ) -> list[dict]:
        events = await self.event_repo.find_by_campaign(campaign_id, event_type=event_type)
        return [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "recipient_email": e.recipient_email,
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in events
        ]

    async def record_event(
        self, campaign_id: UUID, event_type: str, recipient_email: str, metadata: dict | None = None
    ) -> None:
        event = EmailEvent.create(
            campaign_id=campaign_id,
            event_type=event_type,
            recipient_email=recipient_email,
            metadata=metadata,
        )
        await self.event_repo.save(event)

        campaign = await self.campaign_repo.find_by_id(campaign_id)
        if campaign is not None:
            if event_type == "opened":
                campaign.open_count += 1
            elif event_type == "clicked":
                campaign.click_count += 1
            elif event_type == "bounced":
                campaign.bounce_count += 1
            await self.campaign_repo.save(campaign)

    async def delete_campaign(self, campaign_id: UUID) -> None:
        await self.campaign_repo.delete(campaign_id)
