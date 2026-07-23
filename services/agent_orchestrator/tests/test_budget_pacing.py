"""Tests for BudgetPacingService — the core pacing algorithm.

Covers all pacing strategies, status detection, alert generation,
daily schedule generation, and edge cases.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.entities.campaigns.campaign_budget import CampaignBudget
from app.domain.services.campaigns.budget_pacing import (
    BudgetPacingService,
    PacingStatus,
    PacingStrategy,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_campaign(
    start: date,
    end: date,
    name: str = "Test Campaign",
) -> Campaign:
    return Campaign.create(
        organization_id=uuid4(),
        name=name,
        created_by=uuid4(),
        start_date=start,
        end_date=end,
    )


def _make_budget(
    total: float,
    spent: float = 0.0,
    campaign_id: UUID | None = None,
) -> CampaignBudget:
    bid = campaign_id or uuid4()
    b = CampaignBudget.create(
        campaign_id=bid,
        total_budget=total,
    )
    b.spent = spent
    return b


# ── Tests ────────────────────────────────────────────────────────────


class TestEvenPacing:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_on_track(self):
        """50% time elapsed, 50% spent → ON_TRACK."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=5000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.status == PacingStatus.ON_TRACK
        assert 0.95 <= rec.pace_ratio <= 1.05

    def test_ahead(self):
        """50% time, 53% spent → AHEAD (ratio ~1.06)."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=5300)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.status == PacingStatus.AHEAD
        assert rec.pace_ratio > 1.05

    def test_behind(self):
        """50% time, 40% spent → BEHIND."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=4000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.status == PacingStatus.BEHIND
        assert rec.pace_ratio < 0.95

    def test_overspend_risk(self):
        """50% time, 70% spent → OVERSPEND_RISK."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=7000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.status == PacingStatus.OVERSPEND_RISK
        assert rec.pace_ratio >= 1.15

    def test_underspend_risk(self):
        """50% time, 20% spent → UNDERSPEND_RISK."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=2000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.status == PacingStatus.UNDERSPEND_RISK

    def test_completed(self):
        """All time elapsed, 95%+ spent → COMPLETED."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=9600)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 31))

        assert rec.status == PacingStatus.COMPLETED


class TestFrontLoadedPacing:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_higher_early(self):
        """Front-loaded: daily target early > even daily target."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        rec_even = self.service.analyze(campaign, budget, strategy=PacingStrategy.EVEN, today=start)
        rec_front = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.FRONT_LOADED, today=start
        )

        assert rec_front.daily_target > rec_even.daily_target

    def test_lower_late(self):
        """Front-loaded: daily target late < even daily target."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        rec_even = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.EVEN, today=date(2026, 7, 28)
        )
        rec_front = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.FRONT_LOADED, today=date(2026, 7, 28)
        )

        assert rec_front.daily_target < rec_even.daily_target


class TestBackLoadedPacing:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_lower_early(self):
        """Back-loaded: daily target early < even daily target."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        rec_even = self.service.analyze(campaign, budget, strategy=PacingStrategy.EVEN, today=start)
        rec_back = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.BACK_LOADED, today=start
        )

        assert rec_back.daily_target < rec_even.daily_target

    def test_higher_late(self):
        """Back-loaded: daily target late > even daily target."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        rec_even = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.EVEN, today=date(2026, 7, 28)
        )
        rec_back = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.BACK_LOADED, today=date(2026, 7, 28)
        )

        assert rec_back.daily_target > rec_even.daily_target


class TestPauseAndAlerts:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_should_pause_on_overspend(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=7000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.should_pause is True

    def test_should_pause_on_budget_exhausted(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=10000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 15))

        assert rec.should_pause is True

    def test_should_not_pause_on_track(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=5000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.should_pause is False

    def test_alert_message_overspend(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=7500)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.alert_message is not None
        assert "Overspend" in rec.alert_message

    def test_alert_message_underspend(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=2000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.alert_message is not None
        assert "Underspend" in rec.alert_message

    def test_no_alert_on_track(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=5000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.alert_message is None


class TestDailySchedule:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_even_schedule_day_count(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        schedule = self.service.generate_daily_schedule(campaign, budget, PacingStrategy.EVEN)

        assert len(schedule) == 30  # 30 days in July 1-31

    def test_even_schedule_totals(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        schedule = self.service.generate_daily_schedule(campaign, budget, PacingStrategy.EVEN)

        # All targets should be equal
        targets = [s.target for s in schedule]
        assert len(set(targets)) == 1  # All same value

        # Cumulative should approach total budget
        assert schedule[-1].cumulative_target == pytest.approx(30000, rel=0.01)

    def test_front_loaded_first_gt_last(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        schedule = self.service.generate_daily_schedule(
            campaign, budget, PacingStrategy.FRONT_LOADED
        )

        assert schedule[0].target > schedule[-1].target

    def test_back_loaded_first_lt_last(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        schedule = self.service.generate_daily_schedule(
            campaign, budget, PacingStrategy.BACK_LOADED
        )

        assert schedule[0].target < schedule[-1].target


class TestEdgeCases:
    def setup_method(self):
        self.service = BudgetPacingService()

    def test_single_day_campaign(self):
        start = date(2026, 7, 15)
        end = date(2026, 7, 15)
        campaign = _make_campaign(start, end)
        budget = _make_budget(5000)

        rec = self.service.analyze(campaign, budget, today=start)

        assert rec.daily_target == pytest.approx(5000.0)
        assert rec.days_elapsed >= 0

    def test_zero_budget(self):
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(0.01)  # Nearly zero

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        assert rec.total_budget == pytest.approx(0.01)
        assert rec.daily_target >= 0

    def test_campaign_before_start(self):
        """Today is before campaign start date."""
        start = date(2026, 7, 15)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 1))

        assert rec.days_elapsed == 0
        assert rec.percent_time_elapsed == 0.0

    def test_pace_ratio_calculation(self):
        """Verify pace_ratio = spend_pct / time_pct."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(10000, spent=6000)

        rec = self.service.analyze(campaign, budget, today=date(2026, 7, 16))

        # time_pct = 15/30 = 0.5, spend_pct = 6000/10000 = 0.6
        expected_ratio = 0.6 / 0.5
        assert rec.pace_ratio == pytest.approx(expected_ratio, rel=0.01)

    def test_custom_strategy(self):
        """Custom strategy falls back to even."""
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)
        campaign = _make_campaign(start, end)
        budget = _make_budget(30000)

        rec_even = self.service.analyze(campaign, budget, strategy=PacingStrategy.EVEN, today=start)
        rec_custom = self.service.analyze(
            campaign, budget, strategy=PacingStrategy.CUSTOM, today=start
        )

        assert rec_even.daily_target == pytest.approx(rec_custom.daily_target, rel=0.01)
