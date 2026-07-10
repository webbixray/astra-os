from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    SYNCING = "syncing"
    FAILED = "failed"
    NOT_SYNCED = "not_synced"


class CampaignObjective(str, Enum):
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    SALES = "sales"
    RETARGETING = "retargeting"


@dataclass
class AdCampaign:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    ad_account_id: UUID = field(default_factory=uuid4)
    name: str = ""
    objective: CampaignObjective = CampaignObjective.AWARENESS
    status: str = "draft"
    platform_campaign_id: str = ""
    platform: str = ""
    daily_budget: float = 0
    lifetime_budget: float = 0
    currency: str = "USD"
    start_date: str = ""
    end_date: str = ""
    targeting: dict = field(default_factory=dict)
    creatives: list[dict] = field(default_factory=list)
    sync_status: SyncStatus = SyncStatus.NOT_SYNCED
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        ad_account_id: UUID,
        name: str,
        objective: CampaignObjective = CampaignObjective.AWARENESS,
        created_by: UUID | None = None,
    ) -> "AdCampaign":
        return cls(
            organization_id=organization_id,
            ad_account_id=ad_account_id,
            name=name,
            objective=objective,
            created_by=created_by or uuid4(),
        )
