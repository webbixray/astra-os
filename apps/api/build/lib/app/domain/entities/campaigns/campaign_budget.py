from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


@dataclass
class CampaignBudget:
    id: UUID = field(default_factory=uuid4)
    campaign_id: UUID = field(default_factory=uuid4)
    total_budget: float = 0.0
    spent: float = 0.0
    currency: str = "USD"
    alert_threshold: float = 80.0
    period_start: datetime | None = None
    period_end: datetime | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @property
    def remaining(self) -> float:
        return max(0.0, self.total_budget - self.spent)

    @property
    def spend_pct(self) -> float:
        if self.total_budget <= 0:
            return 0.0
        return (self.spent / self.total_budget) * 100.0

    @property
    def is_alert_triggered(self) -> bool:
        return self.spend_pct >= self.alert_threshold

    @classmethod
    def create(
        cls,
        campaign_id: UUID,
        total_budget: float,
        currency: str = "USD",
        alert_threshold: float = 80.0,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> "CampaignBudget":
        if total_budget <= 0:
            raise ValidationError("Total budget must be positive")
        if not (0 <= alert_threshold <= 100):
            raise ValidationError("Alert threshold must be between 0 and 100")
        return cls(
            campaign_id=campaign_id,
            total_budget=total_budget,
            currency=currency,
            alert_threshold=alert_threshold,
            period_start=period_start,
            period_end=period_end,
        )

    def record_spend(self, amount: float) -> None:
        if amount <= 0:
            raise ValidationError("Spend amount must be positive")
        self.spent += amount
        self.updated_at = now()

    def update_budget(self, total_budget: float) -> None:
        if total_budget <= 0:
            raise ValidationError("Total budget must be positive")
        self.total_budget = total_budget
        self.updated_at = now()
