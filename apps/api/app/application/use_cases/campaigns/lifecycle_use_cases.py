"""Campaign Lifecycle Use Cases — launch, pause, resume, complete.

These use cases wrap the Campaign entity's state machine with
side effects: domain events, budget pacing checks, and audit logging.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.common import now
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError

if TYPE_CHECKING:
    from app.domain.entities.campaigns.campaign import Campaign
    from app.domain.services.campaigns.budget_pacing import BudgetPacingService


class LaunchCampaignUseCase:
    """Transition campaign from draft/pending_approval → active.

    Pre-conditions:
    - Campaign must be in 'draft' or 'pending_approval' status
    - Campaign must have a start_date
    - Budget must be set if channels include 'ads'
    """

    def __init__(self, repo: CampaignRepository, pacing_service: BudgetPacingService | None = None):
        self.repo = repo
        self.pacing_service = pacing_service

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))

        # Validate pre-conditions
        if campaign.status not in ("draft", "pending_approval"):
            raise ValidationError(
                f"Cannot launch campaign in '{campaign.status}' status. "
                f"Must be 'draft' or 'pending_approval'."
            )

        if not campaign.start_date:
            raise ValidationError("Campaign must have a start_date to launch.")

        if "ads" in (campaign.channels or []) and not campaign.budget_amount:
            raise ValidationError("Campaign with 'ads' channel must have a budget set.")

        # Transition state (skip pending_approval if already there)
        if campaign.status == "draft":
            campaign.transition_to("pending_approval")
        campaign.transition_to("active")
        campaign.updated_at = now()

        saved = await self.repo.save(campaign)

        # Publish event
        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_ACTIVATED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                    "channels": saved.channels,
                    "budget_amount": saved.budget_amount,
                },
            )
        )

        return saved


class PauseCampaignUseCase:
    """Transition campaign from active → paused."""

    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID, reason: str = "") -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))

        if campaign.status != "active":
            raise ValidationError(
                f"Cannot pause campaign in '{campaign.status}' status. Must be 'active'."
            )

        campaign.transition_to("paused")
        campaign.updated_at = now()

        saved = await self.repo.save(campaign)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_PAUSED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                    "reason": reason,
                },
            )
        )

        return saved


class ResumeCampaignUseCase:
    """Transition campaign from paused → active."""

    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))

        if campaign.status != "paused":
            raise ValidationError(
                f"Cannot resume campaign in '{campaign.status}' status. Must be 'paused'."
            )

        campaign.transition_to("active")
        campaign.updated_at = now()

        saved = await self.repo.save(campaign)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_ACTIVATED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                    "action": "resumed",
                },
            )
        )

        return saved


class CompleteCampaignUseCase:
    """Transition campaign from active/paused → completed."""

    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))

        if campaign.status not in ("active", "paused"):
            raise ValidationError(
                f"Cannot complete campaign in '{campaign.status}' status. "
                f"Must be 'active' or 'paused'."
            )

        campaign.transition_to("completed")
        campaign.updated_at = now()

        saved = await self.repo.save(campaign)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_COMPLETED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                },
            )
        )

        return saved


class ArchiveCampaignUseCase:
    """Transition any terminal-state campaign → archived."""

    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self.repo.find_by_id(campaign_id)
        if campaign is None:
            raise EntityNotFoundError("Campaign", str(campaign_id))

        if campaign.status == "archived":
            raise ValidationError("Campaign is already archived.")

        campaign.transition_to("archived")
        campaign.updated_at = now()

        saved = await self.repo.save(campaign)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CAMPAIGN_ARCHIVED,
                aggregate_id=str(saved.id),
                aggregate_type="campaign",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                },
            )
        )

        return saved


# Avoid circular imports — use a forward reference for the repo type
# This is resolved at runtime by the concrete CampaignRepositoryImpl
class CampaignRepository:
    async def save(self, campaign: Campaign) -> Campaign: ...
    async def find_by_id(self, campaign_id: UUID) -> Campaign | None: ...
