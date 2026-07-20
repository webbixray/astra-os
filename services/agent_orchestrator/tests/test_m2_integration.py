"""M2 Integration Tests — full campaign lifecycle, pacing, creative workflow.

Tests the complete M2 Campaign Execution flow:
1. Create campaign → set budget → calculate pacing → launch → pause → resume → complete
2. Creative lifecycle: create → submit → approve → associate → list
3. Pacing analysis across different strategies
4. Event bus captures all campaign mutations
"""

import asyncio
from datetime import date, timedelta
from uuid import uuid4

from app.domain.entities.advertising.ad_creative import (
    CreativeStatus,
    CreativeType,
)
from app.domain.events.event_bus import DomainEventType, EventBus
from apps.api.app.domain.entities.campaigns.campaign import Campaign
from apps.api.app.domain.entities.campaigns.campaign_budget import CampaignBudget
from apps.api.app.domain.services.campaigns.budget_pacing import (
    BudgetPacingService,
    PacingStatus,
    PacingStrategy,
)

# ── Mock Repository ──────────────────────────────────────────────────


class IntegratedCampaignRepo:
    """In-memory repo that tracks saves for verification."""

    def __init__(self):
        self._campaigns: dict = {}
        self._saves: list = []

    async def save(self, campaign):
        self._campaigns[campaign.id] = campaign
        self._saves.append(campaign.id)
        return campaign

    async def find_by_id(self, campaign_id):
        return self._campaigns.get(campaign_id)

    async def find_by_organization(self, org_id, status=None):
        results = [c for c in self._campaigns.values() if c.organization_id == org_id]
        if status:
            results = [c for c in results if c.status == status]
        return results


class IntegratedCreativeRepo:
    def __init__(self):
        self._creatives: dict = {}

    async def save(self, creative):
        self._creatives[creative.id] = creative
        return creative

    async def find_by_id(self, creative_id):
        return self._creatives.get(creative_id)

    async def find_by_organization(self, org_id, status=None):
        results = [c for c in self._creatives.values() if c.organization_id == org_id]
        if status:
            results = [c for c in results if c.status == status]
        return results

    async def find_by_campaign(self, campaign_id):
        return [c for c in self._creatives.values() if c.ad_campaign_id == campaign_id]

    async def delete(self, creative_id):
        self._creatives.pop(creative_id, None)


# ── Full Campaign Lifecycle Test ─────────────────────────────────────


class TestCampaignLifecycleIntegration:
    """End-to-end test: create → budget → pacing → launch → pause → resume → complete."""

    def test_full_lifecycle(self):
        from app.application.use_cases.campaigns.budget_use_cases import (
            SetCampaignBudgetUseCase,
        )
        from app.application.use_cases.campaigns.campaign_use_cases import (
            CreateCampaignUseCase,
        )
        from app.application.use_cases.campaigns.lifecycle_use_cases import (
            CompleteCampaignUseCase,
            LaunchCampaignUseCase,
            PauseCampaignUseCase,
            ResumeCampaignUseCase,
        )

        async def run():
            # Reset EventBus
            EventBus.reset()

            # Setup
            org_id = uuid4()
            user_id = uuid4()
            campaign_repo = IntegratedCampaignRepo()

            # 1. Create campaign
            create_uc = CreateCampaignUseCase(campaign_repo)
            campaign = await create_uc.execute(
                organization_id=org_id,
                name="Integration Test Campaign",
                created_by=user_id,
                description="Full lifecycle test",
                budget_amount=10000.0,
                channels=["ads", "social"],
                objective="conversion",
                start_date=date.today().isoformat(),
                end_date=(date.today() + timedelta(days=30)).isoformat(),
            )
            assert campaign.status == "draft"
            assert campaign.name == "Integration Test Campaign"
            assert "ads" in campaign.channels

            # 2. Set budget
            budget_repo = _MockBudgetRepo()
            budget_uc = SetCampaignBudgetUseCase(budget_repo)
            budget = await budget_uc.execute(
                campaign_id=campaign.id,
                total_budget=10000.0,
                currency="USD",
                alert_threshold=80.0,
            )
            assert budget.total_budget == 10000.0
            assert budget.remaining == 10000.0

            # 3. Calculate pacing
            pacing_service = BudgetPacingService()
            rec = pacing_service.analyze(campaign, budget, strategy=PacingStrategy.EVEN)
            assert rec.status in (PacingStatus.ON_TRACK, PacingStatus.UNDERSPEND_RISK)
            assert rec.total_budget == 10000.0
            assert rec.daily_target > 0
            assert rec.should_pause is False

            # 4. Launch campaign (draft → pending_approval → active)
            launch_uc = LaunchCampaignUseCase(campaign_repo)
            campaign = await launch_uc.execute(campaign.id)
            assert campaign.status == "active"

            # 5. Pause campaign
            pause_uc = PauseCampaignUseCase(campaign_repo)
            campaign = await pause_uc.execute(campaign.id, reason="Budget review")
            assert campaign.status == "paused"

            # 6. Resume campaign
            resume_uc = ResumeCampaignUseCase(campaign_repo)
            campaign = await resume_uc.execute(campaign.id)
            assert campaign.status == "active"

            # 7. Record spend and re-check pacing
            budget.record_spend(3000.0)
            rec2 = pacing_service.analyze(campaign, budget, strategy=PacingStrategy.EVEN)
            assert rec2.total_spent == 3000.0
            assert rec2.percent_budget_spent == 30.0

            # 8. Complete campaign
            complete_uc = CompleteCampaignUseCase(campaign_repo)
            campaign = await complete_uc.execute(campaign.id)
            assert campaign.status == "completed"

            # 9. Verify events were published
            history = EventBus.get_history()
            event_types = [e.event_type for e in history]
            assert DomainEventType.CAMPAIGN_CREATED in event_types
            assert DomainEventType.CAMPAIGN_ACTIVATED in event_types
            assert DomainEventType.CAMPAIGN_PAUSED in event_types
            assert DomainEventType.CAMPAIGN_COMPLETED in event_types

            # 10. Verify audit trail
            assert len(history) >= 4

            EventBus.reset()

        asyncio.run(run())


# ── Creative Lifecycle Integration ───────────────────────────────────


class TestCreativeLifecycleIntegration:
    """End-to-end test: create → submit → approve → associate → list."""

    def test_full_creative_lifecycle(self):
        from app.application.use_cases.campaigns.creative_use_cases import (
            ApproveCreativeUseCase,
            AssociateCreativeToCampaignUseCase,
            CreateCreativeUseCase,
            ListCreativesByCampaignUseCase,
            SubmitCreativeForReviewUseCase,
            UpdateCreativeUseCase,
        )

        async def run():
            EventBus.reset()

            org_id = uuid4()
            campaign_id = uuid4()
            user_id = uuid4()
            repo = IntegratedCreativeRepo()

            # 1. Create creative
            create_uc = CreateCreativeUseCase(repo)
            creative = await create_uc.execute(
                organization_id=org_id,
                name="Summer Sale Banner",
                created_by=user_id,
                type=CreativeType.IMAGE,
                headline="50% Off Everything!",
                body="Limited time offer. Shop now.",
                destination_url="https://example.com/sale",
            )
            assert creative.status == CreativeStatus.DRAFT
            assert creative.name == "Summer Sale Banner"

            # 2. Update creative
            update_uc = UpdateCreativeUseCase(repo)
            creative = await update_uc.execute(
                creative_id=creative.id,
                headline="60% Off Everything!",
            )
            assert creative.headline == "60% Off Everything!"

            # 3. Submit for review
            submit_uc = SubmitCreativeForReviewUseCase(repo)
            creative = await submit_uc.execute(creative.id)
            assert creative.status == CreativeStatus.PENDING_REVIEW

            # 4. Approve
            approve_uc = ApproveCreativeUseCase(repo)
            creative = await approve_uc.execute(creative.id)
            assert creative.status == CreativeStatus.APPROVED

            # 5. Associate with campaign
            assoc_uc = AssociateCreativeToCampaignUseCase(repo)
            creative = await assoc_uc.execute(creative.id, campaign_id)
            assert creative.ad_campaign_id == campaign_id

            # 6. List by campaign
            list_uc = ListCreativesByCampaignUseCase(repo)
            creatives = await list_uc.execute(campaign_id)
            assert len(creatives) == 1
            assert creatives[0].id == creative.id

            # 7. Verify events
            history = EventBus.get_history()
            event_types = [e.event_type for e in history]
            assert DomainEventType.CONTENT_CREATED in event_types
            assert DomainEventType.CONTENT_APPROVED in event_types

            EventBus.reset()

        asyncio.run(run())


# ── Pacing Integration ───────────────────────────────────────────────


class TestPacingIntegration:
    """Test pacing analysis across full campaign lifecycle."""

    def test_pacing_with_spend_progression(self):
        """Simulate daily spend and verify pacing recommendations change."""
        service = BudgetPacingService()
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)

        campaign = Campaign.create(
            organization_id=uuid4(),
            name="Pacing Test",
            created_by=uuid4(),
            start_date=start,
            end_date=end,
        )
        budget = CampaignBudget.create(
            campaign_id=campaign.id,
            total_budget=30000.0,
        )

        # Day 1: no spend → underspend risk
        rec = service.analyze(campaign, budget, today=start)
        assert rec.status == PacingStatus.UNDERSPEND_RISK

        # Day 11: 10/30 days elapsed = 33%, 33% spent → on track
        budget.spent = 10000.0
        rec = service.analyze(campaign, budget, today=date(2026, 7, 11))
        assert rec.status == PacingStatus.ON_TRACK

        # Day 16: 15/30 days elapsed = 50%, 55% spent → ahead
        budget.spent = 16500.0
        rec = service.analyze(campaign, budget, today=date(2026, 7, 16))
        assert rec.status == PacingStatus.AHEAD

        # Day 21: 20/30 days elapsed = 67%, 85% spent → overspend risk
        budget.spent = 25500.0
        rec = service.analyze(campaign, budget, today=date(2026, 7, 21))
        assert rec.status == PacingStatus.OVERSPEND_RISK
        assert rec.should_pause is True

    def test_pacing_strategies_give_different_schedules(self):
        """Verify even, front-loaded, back-loaded produce different daily targets."""
        service = BudgetPacingService()
        start = date(2026, 7, 1)
        end = date(2026, 7, 31)

        campaign = Campaign.create(
            organization_id=uuid4(),
            name="Strategy Comparison",
            created_by=uuid4(),
            start_date=start,
            end_date=end,
        )
        budget = CampaignBudget.create(
            campaign_id=campaign.id,
            total_budget=30000.0,
        )

        rec_even = service.analyze(campaign, budget, strategy=PacingStrategy.EVEN, today=start)
        rec_front = service.analyze(
            campaign, budget, strategy=PacingStrategy.FRONT_LOADED, today=start
        )
        rec_back = service.analyze(
            campaign, budget, strategy=PacingStrategy.BACK_LOADED, today=start
        )

        # Front-loaded should have higher daily target than even on day 1
        assert rec_front.daily_target > rec_even.daily_target
        # Back-loaded should have lower daily target than even on day 1
        assert rec_back.daily_target < rec_even.daily_target

        # All should have same totals
        assert rec_even.total_budget == rec_front.total_budget == rec_back.total_budget


# ── Budget + Pacing Edge Cases ───────────────────────────────────────


class TestBudgetPacingEdgeCases:
    def test_budget_exhausted_triggers_pause(self):
        service = BudgetPacingService()
        campaign = Campaign.create(
            organization_id=uuid4(),
            name="Exhausted",
            created_by=uuid4(),
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        budget = CampaignBudget.create(
            campaign_id=campaign.id,
            total_budget=5000.0,
        )
        budget.spent = 5000.0

        rec = service.analyze(campaign, budget, today=date(2026, 7, 15))
        assert rec.should_pause is True
        assert rec.remaining_budget == 0.0

    def test_alert_threshold_triggers_pause(self):
        service = BudgetPacingService()
        campaign = Campaign.create(
            organization_id=uuid4(),
            name="Alert Test",
            created_by=uuid4(),
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        budget = CampaignBudget.create(
            campaign_id=campaign.id,
            total_budget=10000.0,
            alert_threshold=70.0,
        )
        budget.spent = 7500.0  # 75% > 70% threshold

        rec = service.analyze(campaign, budget, today=date(2026, 7, 16))
        assert rec.should_pause is True


# ── Helper: Mock Budget Repo ─────────────────────────────────────────


class _MockBudgetRepo:
    def __init__(self):
        self._budgets = {}

    async def save(self, budget):
        self._budgets[budget.campaign_id] = budget
        return budget

    async def find_by_campaign(self, campaign_id):
        return self._budgets.get(campaign_id)

    async def find_by_id(self, budget_id):
        for b in self._budgets.values():
            if b.id == budget_id:
                return b
        return None
