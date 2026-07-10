from uuid import UUID

from app.domain.entities.campaigns.campaign_budget import CampaignBudget
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


class CampaignBudgetRepository:
    async def save(self, budget: CampaignBudget) -> CampaignBudget: ...
    async def find_by_campaign(self, campaign_id: UUID) -> CampaignBudget | None: ...
    async def find_by_id(self, budget_id: UUID) -> CampaignBudget | None: ...


class SetCampaignBudgetUseCase:
    def __init__(self, repo: CampaignBudgetRepository):
        self.repo = repo

    async def execute(
        self,
        campaign_id: UUID,
        total_budget: float,
        currency: str = "USD",
        alert_threshold: float = 80.0,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> CampaignBudget:
        existing = await self.repo.find_by_campaign(campaign_id)
        if existing:
            existing.update_budget(total_budget)
            existing.currency = currency
            existing.alert_threshold = alert_threshold
            return await self.repo.save(existing)

        from datetime import datetime as dt
        budget = CampaignBudget.create(
            campaign_id=campaign_id,
            total_budget=total_budget,
            currency=currency,
            alert_threshold=alert_threshold,
            period_start=dt.fromisoformat(period_start) if period_start else None,
            period_end=dt.fromisoformat(period_end) if period_end else None,
        )
        return await self.repo.save(budget)


class GetCampaignBudgetUseCase:
    def __init__(self, repo: CampaignBudgetRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID) -> CampaignBudget:
        budget = await self.repo.find_by_campaign(campaign_id)
        if budget is None:
            raise EntityNotFoundError("CampaignBudget", str(campaign_id))
        return budget


class RecordSpendUseCase:
    def __init__(self, repo: CampaignBudgetRepository):
        self.repo = repo

    async def execute(self, campaign_id: UUID, amount: float) -> CampaignBudget:
        budget = await self.repo.find_by_campaign(campaign_id)
        if budget is None:
            raise EntityNotFoundError("CampaignBudget", str(campaign_id))
        budget.record_spend(amount)
        return await self.repo.save(budget)
