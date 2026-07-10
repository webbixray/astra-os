from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.entities.campaigns.campaign import Campaign
from app.domain.entities.campaigns.campaign_template import CampaignTemplate
from app.domain.exceptions.domain_exceptions import EntityNotFoundError

if TYPE_CHECKING:
    from uuid import UUID


class CampaignTemplateRepository:
    async def save(self, template: CampaignTemplate) -> CampaignTemplate: ...
    async def find_by_id(self, template_id: UUID) -> CampaignTemplate | None: ...
    async def find_by_organization(self, org_id: UUID) -> list[CampaignTemplate]: ...
    async def delete(self, template_id: UUID) -> None: ...


class CreateTemplateUseCase:
    def __init__(self, repo: CampaignTemplateRepository):
        self.repo = repo

    async def execute(
        self,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        description: str = "",
        channels: list[str] | None = None,
        objective: str | None = None,
        budget_amount: float | None = None,
        budget_currency: str = "USD",
        default_duration_days: int = 30,
        config: dict | None = None,
    ) -> CampaignTemplate:
        template = CampaignTemplate.create(
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            description=description,
            channels=channels,
            objective=objective,
            budget_amount=budget_amount,
            budget_currency=budget_currency,
            default_duration_days=default_duration_days,
            config=config,
        )
        return await self.repo.save(template)


class ListTemplatesUseCase:
    def __init__(self, repo: CampaignTemplateRepository):
        self.repo = repo

    async def execute(self, org_id: UUID) -> list[CampaignTemplate]:
        return await self.repo.find_by_organization(org_id)


class GetTemplateUseCase:
    def __init__(self, repo: CampaignTemplateRepository):
        self.repo = repo

    async def execute(self, template_id: UUID) -> CampaignTemplate:
        template = await self.repo.find_by_id(template_id)
        if template is None:
            raise EntityNotFoundError("CampaignTemplate", str(template_id))
        return template


class DeleteTemplateUseCase:
    def __init__(self, repo: CampaignTemplateRepository):
        self.repo = repo

    async def execute(self, template_id: UUID) -> None:
        await self.repo.delete(template_id)


class CampaignRepository:
    async def save(self, campaign: Campaign) -> Campaign: ...
    async def find_by_id(self, campaign_id: UUID) -> Campaign | None: ...
    async def find_by_organization(self, org_id: UUID, status: str | None = None) -> list[Campaign]: ...
    async def delete(self, campaign_id: UUID) -> None: ...


class CloneCampaignFromTemplateUseCase:
    def __init__(self, template_repo: CampaignTemplateRepository, campaign_repo: CampaignRepository):
        self.template_repo = template_repo
        self.campaign_repo = campaign_repo

    async def execute(
        self,
        template_id: UUID,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        start_date: str | None = None,
    ) -> Campaign:
        template = await self.template_repo.find_by_id(template_id)
        if template is None:
            raise EntityNotFoundError("CampaignTemplate", str(template_id))

        from datetime import date

        campaign = Campaign.create(
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            description=template.description,
            budget_amount=template.budget_amount,
            budget_currency=template.budget_currency,
            channels=list(template.channels),
            objective=template.objective,
            start_date=date.fromisoformat(start_date) if start_date else date.today(),  # noqa: DTZ011
            end_date=None,
        )
        return await self.campaign_repo.save(campaign)
