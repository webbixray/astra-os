from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

AB_TEST_STATUSES = ["draft", "running", "paused", "completed", "archived"]


@dataclass
class ABTestVariant:
    id: UUID = field(default_factory=uuid4)
    ab_test_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    config: dict = field(default_factory=dict)
    traffic_percent: float = 50.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    created_at: datetime = field(default_factory=now)

    @property
    def ctr(self) -> float:
        if self.impressions <= 0:
            return 0.0
        return (self.clicks / self.impressions) * 100.0

    @property
    def conversion_rate(self) -> float:
        if self.clicks <= 0:
            return 0.0
        return (self.conversions / self.clicks) * 100.0

    @property
    def cpa(self) -> float:
        if self.conversions <= 0:
            return 0.0
        return self.spend / self.conversions

    @classmethod
    def create(
        cls,
        ab_test_id: UUID,
        name: str,
        description: str = "",
        config: dict | None = None,
        traffic_percent: float = 50.0,
    ) -> "ABTestVariant":
        if not name or not name.strip():
            raise ValidationError("Variant name is required")
        if not (0 < traffic_percent <= 100):
            raise ValidationError("Traffic percent must be between 0 and 100")
        return cls(
            ab_test_id=ab_test_id,
            name=name,
            description=description,
            config=config or {},
            traffic_percent=traffic_percent,
        )


@dataclass
class ABTest:
    id: UUID = field(default_factory=uuid4)
    campaign_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    status: str = "draft"
    goal_metric: str = "conversion_rate"
    winner_variant_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_by: UUID = field(default_factory=uuid4)
    variants: list[ABTestVariant] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    VALID_GOAL_METRICS: ClassVar[list[str]] = [
        "ctr",
        "conversion_rate",
        "cpa",
        "clicks",
        "conversions",
    ]

    @classmethod
    def create(
        cls,
        campaign_id: UUID,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        description: str = "",
        goal_metric: str = "conversion_rate",
    ) -> "ABTest":
        if not name or not name.strip():
            raise ValidationError("Test name is required")
        if goal_metric not in cls.VALID_GOAL_METRICS:
            raise ValidationError(f"Invalid goal metric: {goal_metric}")
        return cls(
            campaign_id=campaign_id,
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            description=description,
            goal_metric=goal_metric,
        )

    def add_variant(self, variant: ABTestVariant) -> None:
        total_traffic = sum(v.traffic_percent for v in self.variants) + variant.traffic_percent
        if total_traffic > 100:
            raise ValidationError(f"Total traffic allocation would exceed 100% ({total_traffic}%)")
        self.variants.append(variant)
        self.updated_at = now()

    def start(self) -> None:
        if self.status != "draft":
            raise ValidationError(f"Cannot start test in '{self.status}' status")
        if len(self.variants) < 2:
            raise ValidationError("Need at least 2 variants to start")
        self.status = "running"
        self.start_date = now()
        self.updated_at = now()

    def determine_winner(self) -> ABTestVariant | None:
        if not self.variants:
            return None
        best = max(
            self.variants,
            key=lambda v: (
                v.conversion_rate
                if self.goal_metric == "conversion_rate"
                else v.ctr
                if self.goal_metric == "ctr"
                else -v.cpa
                if self.goal_metric == "cpa"
                else v.clicks
                if self.goal_metric == "clicks"
                else v.conversions
            ),
        )
        self.winner_variant_id = best.id
        self.status = "completed"
        self.end_date = now()
        self.updated_at = now()
        return best
