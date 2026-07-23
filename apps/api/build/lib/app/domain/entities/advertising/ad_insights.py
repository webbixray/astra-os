from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now


@dataclass
class AdInsight:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    ad_account_id: UUID = field(default_factory=uuid4)
    ad_campaign_id: UUID | None = None
    date: str = ""
    impressions: int = 0
    clicks: int = 0
    spend: float = 0
    conversions: int = 0
    revenue: float = 0
    platform: str = ""
    created_at: datetime = field(default_factory=now)

    @property
    def ctr(self) -> float:
        return round(self.clicks / self.impressions * 100, 2) if self.impressions > 0 else 0

    @property
    def cpc(self) -> float:
        return round(self.spend / self.clicks, 2) if self.clicks > 0 else 0

    @property
    def conversion_rate(self) -> float:
        return round(self.conversions / self.clicks * 100, 2) if self.clicks > 0 else 0

    @property
    def roas(self) -> float:
        return round(self.revenue / self.spend, 2) if self.spend > 0 else 0
