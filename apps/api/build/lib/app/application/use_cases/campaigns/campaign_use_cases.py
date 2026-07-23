from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.common import now
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from uuid import UUID
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


class CampaignRepository:
    async def save(self, campaign: Campaign) -> Campaign: ...

    async def find_by_id(self, campaign_id: UUID) -> Campaign | None: ...

    async def find_by_organization(
        self, org_id: UUID, status: str | None = None
    ) -> list[Campaign]: ...

    async def delete(self, campaign_id: UUID) -> None: ...


class CreateCampaignUseCase:
    def __init__(
        self,
        repo: CampaignRepository,
        member_check: Callable[[UUID], Awaitable[bool]] | None = None,
    ):
        self.repo = repo
        self.member_check = member_check

    async def execute(
        self,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        description: str | None = None,
        budget_amount: float | None = None,
        budget_currency: str = "USD",
        start_date: str | None = None,
        end_date: str | None = None,
        channels: list[str] | None = None,
        objective: str | None = None,
    ) -> Campaign:
        from datetime import date as d

        start = d.fromisoformat(start_date) if start_date else None
        end = d.fromisoformat(end_date) if end_date else None
        campaign = Campaign.create(
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            description=description,
            budget_amount=budget_amount,
            budget_currency=budget_currency,
            start_date=start,
            end_date=end,
            channels=channels,
            objective=objective,
        )
        saved = await self.repo.save(campaign)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_CREATED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(organization_id),
                    "name": name,
                    "created_by": str(created_by),
                },
            )
        )

        return saved


class GetCampaignUseCase:
    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))
        return campaign


class ListCampaignsUseCase:
    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, org_id: UUID, status: str | None = None) -> list[Campaign]:
        return await self.repo.find_by_organization(org_id, status=status)


class UpdateCampaignUseCase:
    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(
        self,
        campaign_id: UUID,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        budget_amount: float | None = None,
    ) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))
        if name is not None:
            campaign.name = name
        if description is not None:
            campaign.description = description
        if status is not None:
            campaign.transition_to(status)
        if budget_amount is not None:
            campaign.update_budget(budget_amount)
        campaign.updated_at = now()
        return await self.repo.save(campaign)
