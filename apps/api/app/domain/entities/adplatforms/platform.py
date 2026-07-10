from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class AdPlatform(str, Enum):
    GOOGLE_ADS = "google_ads"
    META = "meta"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    TWITTER = "twitter"


class AdStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class AdCampaign:
    id: str = ""
    platform: AdPlatform = AdPlatform.GOOGLE_ADS
    name: str = ""
    status: AdStatus = AdStatus.DRAFT
    budget: float = 0
    currency: str = "USD"
    spend: float = 0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0
    start_date: str = ""
    end_date: str = ""
    platform_campaign_id: str = ""


@dataclass
class AdAccount:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    platform: AdPlatform = AdPlatform.GOOGLE_ADS
    account_name: str = ""
    platform_account_id: str = ""
    credentials: dict = field(default_factory=dict)
    is_connected: bool = False
    last_synced_at: datetime | None = None
    created_at: datetime = field(default_factory=now)
