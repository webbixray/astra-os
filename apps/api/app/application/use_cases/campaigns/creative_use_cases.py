"""Creative Management Use Cases — CRUD, approval workflow, campaign association.

Manages AdCreative entities: create, update, approve/reject,
associate with campaigns, and list/search.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.common import now
from app.domain.entities.advertising.ad_creative import (
    AdCreative,
    CreativeStatus,
    CreativeType,
)
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class CreativeRepository:
    async def save(self, creative: AdCreative) -> AdCreative: ...
    async def find_by_id(self, creative_id: UUID) -> AdCreative | None: ...
    async def find_by_organization(
        self, org_id: UUID, status: CreativeStatus | None = None
    ) -> list[AdCreative]: ...
    async def find_by_campaign(self, campaign_id: UUID) -> list[AdCreative]: ...
    async def delete(self, creative_id: UUID) -> None: ...


class CreateCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(
        self,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        type: CreativeType = CreativeType.IMAGE,
        headline: str = "",
        body: str = "",
        destination_url: str = "",
        asset_urls: list[str] | None = None,
    ) -> AdCreative:
        if not name or not name.strip():
            raise ValidationError("Creative name is required")

        creative = AdCreative(
            organization_id=organization_id,
            name=name.strip(),
            type=type,
            created_by=created_by,
            headline=headline,
            body=body,
            destination_url=destination_url,
            asset_urls=asset_urls or [],
        )

        saved = await self.repo.save(creative)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CONTENT_CREATED,
                aggregate_id=str(saved.id),
                aggregate_type="ad_creative",
                data={
                    "organization_id": str(organization_id),
                    "name": name,
                    "type": type.value,
                    "created_by": str(created_by),
                },
            )
        )

        return saved


class GetCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID) -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))
        return creative


class ListCreativesUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(
        self,
        org_id: UUID,
        status: CreativeStatus | None = None,
    ) -> list[AdCreative]:
        return await self.repo.find_by_organization(org_id, status=status)


class ListCreativesByCampaignUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> list[AdCreative]:
        return await self.repo.find_by_campaign(campaign_id)


class UpdateCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(
        self,
        creative_id: UUID,
        name: str | None = None,
        headline: str | None = None,
        body: str | None = None,
        destination_url: str | None = None,
        asset_urls: list[str] | None = None,
    ) -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        if creative.status not in (CreativeStatus.DRAFT, CreativeStatus.REJECTED):
            raise ValidationError(
                f"Cannot edit creative in '{creative.status.value}' status. "
                f"Only 'draft' or 'rejected' creatives can be edited."
            )

        if name is not None:
            creative.name = name.strip()
        if headline is not None:
            creative.headline = headline
        if body is not None:
            creative.body = body
        if destination_url is not None:
            creative.destination_url = destination_url
        if asset_urls is not None:
            creative.asset_urls = asset_urls
        creative.updated_at = now()

        return await self.repo.save(creative)


class ApproveCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID) -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        if creative.status != CreativeStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot approve creative in '{creative.status.value}' status. "
                f"Must be 'pending_review'."
            )

        creative.approve()
        saved = await self.repo.save(creative)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CONTENT_APPROVED,
                aggregate_id=str(saved.id),
                aggregate_type="ad_creative",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                },
            )
        )

        return saved


class RejectCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID, reason: str = "") -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        if creative.status != CreativeStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot reject creative in '{creative.status.value}' status. "
                f"Must be 'pending_review'."
            )

        creative.reject(reason=reason)
        saved = await self.repo.save(creative)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.CONTENT_REJECTED,
                aggregate_id=str(saved.id),
                aggregate_type="ad_creative",
                data={
                    "organization_id": str(saved.organization_id),
                    "name": saved.name,
                    "reason": reason,
                },
            )
        )

        return saved


class SubmitCreativeForReviewUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID) -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        if creative.status != CreativeStatus.DRAFT:
            raise ValidationError(
                f"Cannot submit creative in '{creative.status.value}' status for review. "
                f"Must be 'draft'."
            )

        creative.status = CreativeStatus.PENDING_REVIEW
        creative.updated_at = now()

        return await self.repo.save(creative)


class AssociateCreativeToCampaignUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID, campaign_id: UUID) -> AdCreative:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        creative.ad_campaign_id = campaign_id
        creative.updated_at = now()

        return await self.repo.save(creative)


class DeleteCreativeUseCase:
    def __init__(self, repo: CreativeRepository):
        self.repo = repo

    async def execute(self, creative_id: UUID) -> None:
        creative = await self.repo.find_by_id(creative_id)
        if creative is None:
            raise EntityNotFoundError("AdCreative", str(creative_id))

        if creative.status in (CreativeStatus.ACTIVE,):
            raise ValidationError("Cannot delete an active creative. Pause or archive it first.")

        await self.repo.delete(creative_id)
