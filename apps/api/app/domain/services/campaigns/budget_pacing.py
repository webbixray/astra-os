"""Budget Pacing Service — controls spend rate to prevent overspend.

Pacing strategies:
- EVEN: spend budget uniformly across the campaign duration
- FRONT_LOADED: spend more early, taper off (useful for launches)
- BACK_LOADED: spend more later (useful for seasonal campaigns)
- CUSTOM: user-defined daily caps

The service calculates daily spend targets, detects overspend,
and recommends throttling actions. It is stateless — all state
lives in CampaignBudget + Campaign entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.campaigns.campaign import Campaign
    from app.domain.entities.campaigns.campaign_budget import CampaignBudget


class PacingStrategy(str, Enum):
    EVEN = "even"
    FRONT_LOADED = "front_loaded"
    BACK_LOADED = "back_loaded"
    CUSTOM = "custom"


class PacingStatus(str, Enum):
    ON_TRACK = "on_track"
    AHEAD = "ahead"
    BEHIND = "behind"
    OVERSPEND_RISK = "overspend_risk"
    UNDERSPEND_RISK = "underspend_risk"
    COMPLETED = "completed"


@dataclass
class PacingRecommendation:
    """Output of pacing analysis for a single campaign."""

    campaign_id: str
    strategy: PacingStrategy
    status: PacingStatus
    daily_target: float
    today_spend: float
    total_budget: float
    total_spent: float
    remaining_budget: float
    days_elapsed: int
    days_remaining: int
    percent_time_elapsed: float
    percent_budget_spent: float
    pace_ratio: float  # spend_pct / time_pct — 1.0 = perfect pace
    recommended_daily_limit: float
    should_pause: bool
    alert_message: str | None = None


@dataclass
class DailyPacingTarget:
    """A single day's spend target."""

    day: date
    target: float
    cumulative_target: float


class BudgetPacingService:
    """Stateless service that computes pacing recommendations.

    Usage:
        service = BudgetPacingService()
        rec = service.analyze(campaign, budget, strategy=PacingStrategy.EVEN)
    """

    # Thresholds
    OVERSPEND_RISK_RATIO = 1.15   # 15% ahead of pace → overspend risk
    UNDERSPEND_THRESHOLD = 0.70   # 30% behind pace → underspend risk
    AHEAD_THRESHOLD = 1.05        # 5% ahead → ahead
    BEHIND_THRESHOLD = 0.95       # 5% behind → behind
    MAX_DAILY_MULTIPLIER = 1.5    # never recommend >150% of even daily pace

    def analyze(
        self,
        campaign: Campaign,
        budget: CampaignBudget,
        strategy: PacingStrategy = PacingStrategy.EVEN,
        *,
        today: date | None = None,
        today_spend: float = 0.0,
    ) -> PacingRecommendation:
        """Analyze current pacing and return recommendation.

        Args:
            campaign: The campaign entity (provides dates).
            budget: The campaign budget entity (provides totals/spend).
            strategy: Pacing strategy to apply.
            today: Override for current date (useful in tests).
            today_spend: How much was spent today so far.

        """
        today = today or date.today()
        total_budget = budget.total_budget
        total_spent = budget.spent
        remaining = budget.remaining

        # Calculate campaign duration
        start = campaign.start_date or campaign.created_at.date()
        end = campaign.end_date or start

        total_days = max((end - start).days, 1)
        days_elapsed = max((today - start).days, 0)
        days_remaining = max((end - today).days, 0)
        days_elapsed = min(days_elapsed, total_days)

        # Percentages
        pct_time = days_elapsed / total_days if total_days > 0 else 1.0
        pct_spent = total_spent / total_budget if total_budget > 0 else 0.0

        # Pace ratio: 1.0 = perfect, >1 = overspending, <1 = underspending
        pace_ratio = pct_spent / pct_time if pct_time > 0 else 0.0

        # Even daily target
        even_daily = total_budget / total_days if total_days > 0 else total_budget

        # Strategy-specific daily target
        daily_target = self._compute_daily_target(
            strategy=strategy,
            total_budget=total_budget,
            total_days=total_days,
            days_elapsed=days_elapsed,
        )

        # Recommended daily limit (capped to prevent runaway spend)
        recommended_limit = min(
            daily_target * self.MAX_DAILY_MULTIPLIER,
            remaining,
        )

        # Determine status
        status = self._determine_status(
            pace_ratio=pace_ratio,
            pct_time=pct_time,
            pct_spent=pct_spent,
            days_remaining=days_remaining,
        )

        # Should we pause?
        should_pause = (
            status == PacingStatus.OVERSPEND_RISK
            or budget.is_alert_triggered
            or remaining <= 0
        )

        # Alert message
        alert = self._build_alert(status, pace_ratio, pct_spent, pct_time, remaining)

        return PacingRecommendation(
            campaign_id=str(campaign.id),
            strategy=strategy,
            status=status,
            daily_target=round(daily_target, 2),
            today_spend=today_spend,
            total_budget=total_budget,
            total_spent=total_spent,
            remaining_budget=remaining,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
            percent_time_elapsed=round(pct_time * 100, 2),
            percent_budget_spent=round(pct_spent * 100, 2),
            pace_ratio=round(pace_ratio, 4),
            recommended_daily_limit=round(recommended_limit, 2),
            should_pause=should_pause,
            alert_message=alert,
        )

    def generate_daily_schedule(
        self,
        campaign: Campaign,
        budget: CampaignBudget,
        strategy: PacingStrategy = PacingStrategy.EVEN,
    ) -> list[DailyPacingTarget]:
        """Generate a day-by-day spending schedule for the campaign.

        Returns a list of DailyPacingTarget, one per day of the campaign.
        """
        start = campaign.start_date or campaign.created_at.date()
        end = campaign.end_date or start
        total_days = max((end - start).days, 1)
        total_budget = budget.total_budget

        schedule: list[DailyPacingTarget] = []
        cumulative = 0.0

        for day_offset in range(total_days):
            day = date.fromordinal(start.toordinal() + day_offset)
            target = self._compute_daily_target(
                strategy=strategy,
                total_budget=total_budget,
                total_days=total_days,
                days_elapsed=day_offset,
            )
            cumulative += target
            schedule.append(
                DailyPacingTarget(
                    day=day,
                    target=round(target, 2),
                    cumulative_target=round(cumulative, 2),
                )
            )

        return schedule

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_daily_target(
        self,
        strategy: PacingStrategy,
        total_budget: float,
        total_days: int,
        days_elapsed: int,
    ) -> float:
        if total_days <= 0:
            return total_budget

        if strategy == PacingStrategy.EVEN:
            return total_budget / total_days

        if strategy == PacingStrategy.FRONT_LOADED:
            # Quadratic curve — spend more early
            # remaining_weight for day d = (total_days - d)^2
            # daily = budget * remaining_weight / sum(all weights)
            remaining_weight = (total_days - days_elapsed) ** 2
            total_weight = sum((total_days - i) ** 2 for i in range(total_days))
            return total_budget * remaining_weight / total_weight if total_weight > 0 else total_budget / total_days

        if strategy == PacingStrategy.BACK_LOADED:
            # Inverse of front-loaded — spend more later
            elapsed_weight = (days_elapsed + 1) ** 2
            total_weight = sum((i + 1) ** 2 for i in range(total_days))
            return total_budget * elapsed_weight / total_weight if total_weight > 0 else total_budget / total_days

        # CUSTOM or unknown → fall back to even
        return total_budget / total_days

    def _determine_status(
        self,
        pace_ratio: float,
        pct_time: float,
        pct_spent: float,
        days_remaining: int,
    ) -> PacingStatus:
        if days_remaining <= 0 and pct_spent >= 0.95:
            return PacingStatus.COMPLETED

        if pace_ratio >= self.OVERSPEND_RISK_RATIO:
            return PacingStatus.OVERSPEND_RISK

        if pct_spent <= 0 and pct_time > 0.1:
            return PacingStatus.UNDERSPEND_RISK

        if pace_ratio >= self.AHEAD_THRESHOLD:
            return PacingStatus.AHEAD

        if pace_ratio <= self.BEHIND_THRESHOLD:
            if pace_ratio <= self.UNDERSPEND_THRESHOLD:
                return PacingStatus.UNDERSPEND_RISK
            return PacingStatus.BEHIND

        return PacingStatus.ON_TRACK

    def _build_alert(
        self,
        status: PacingStatus,
        pace_ratio: float,
        pct_spent: float,
        pct_time: float,
        remaining: float,
    ) -> str | None:
        if status == PacingStatus.OVERSPEND_RISK:
            return (
                f"⚠️ Overspend risk: spending at {pace_ratio:.0%} of target pace. "
                f"Consider pausing or reducing daily budget."
            )
        if status == PacingStatus.UNDERSPEND_RISK:
            return (
                f"📉 Underspend risk: only {pct_spent:.1%} budget used "
                f"with {pct_time:.1%} time elapsed. Consider increasing bid or broadening targeting."
            )
        if status == PacingStatus.AHEAD:
            return (
                f"📈 Slightly ahead of pace ({pace_ratio:.0%}). "
                f"Monitor closely to avoid overspend."
            )
        if status == PacingStatus.BEHIND:
            return (
                f"📉 Slightly behind pace ({pace_ratio:.0%}). "
                f"Remaining budget: ${remaining:,.2f}."
            )
        return None
