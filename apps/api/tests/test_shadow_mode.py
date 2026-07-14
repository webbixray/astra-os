"""Tests for Shadow Mode — E6.2 Beta Launch."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.entities.shadow_mode import (
    ComparisonResult,
    DecisionType,
    LiftMeasurement,
    ShadowDecision,
    ShadowEvent,
    ShadowEventType,
    ShadowModeStatus,
    ShadowSession,
)
from app.domain.services.shadow_mode import (
    LiftMeasurementService,
    ShadowDecisionService,
    ShadowSessionService,
)

# --- Mock Repositories ---

class MockSessionRepository:
    def __init__(self):
        self.sessions: dict = {}

    async def save(self, session: ShadowSession) -> ShadowSession:
        self.sessions[session.id] = session
        return session

    async def find_by_id(self, session_id: uuid4) -> ShadowSession | None:
        return self.sessions.get(session_id)

    async def find_by_organization(
        self,
        org_id: uuid4,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]:
        results = [s for s in self.sessions.values() if s.organization_id == org_id]
        if status:
            results = [s for s in results if s.status == status]
        return results[:limit]

    async def list_all(
        self,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]:
        results = list(self.sessions.values())
        if status:
            results = [s for s in results if s.status == status]
        return results[:limit]


class MockDecisionRepository:
    def __init__(self):
        self.decisions: dict = {}

    async def save(self, decision: ShadowDecision) -> ShadowDecision:
        self.decisions[decision.id] = decision
        return decision

    async def find_by_id(self, decision_id: uuid4) -> ShadowDecision | None:
        return self.decisions.get(decision_id)

    async def find_by_session(
        self,
        session_id: uuid4,
        limit: int = 100,
    ) -> list[ShadowDecision]:
        results = [d for d in self.decisions.values() if d.shadow_session_id == session_id]
        results.sort(key=lambda d: d.created_at, reverse=True)
        return results[:limit]

    async def find_pending_comparison(
        self,
        session_id: uuid4,
        limit: int = 50,
    ) -> list[ShadowDecision]:
        results = [
            d for d in self.decisions.values()
            if d.shadow_session_id == session_id and not d.has_human_decision()
        ]
        return results[:limit]

    async def find_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 10,
    ) -> list[ShadowDecision]:
        results = [
            d for d in self.decisions.values()
            if d.entity_type == entity_type and d.entity_id == entity_id
        ]
        return results[:limit]


class MockEventRepository:
    def __init__(self):
        self.events: dict = {}

    async def save(self, event: ShadowEvent) -> ShadowEvent:
        self.events[event.id] = event
        return event

    async def find_by_session(
        self,
        session_id: uuid4,
        event_type: ShadowEventType | None = None,
        limit: int = 100,
    ) -> list[ShadowEvent]:
        results = [e for e in self.events.values() if e.shadow_session_id == session_id]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        results.sort(key=lambda e: e.created_at, reverse=True)
        return results[:limit]


class MockLiftRepository:
    def __init__(self):
        self.measurements: dict = {}

    async def save(self, measurement: LiftMeasurement) -> LiftMeasurement:
        self.measurements[measurement.id] = measurement
        return measurement

    async def find_by_session(
        self,
        session_id: uuid4,
        limit: int = 50,
    ) -> list[LiftMeasurement]:
        results = [m for m in self.measurements.values() if m.shadow_session_id == session_id]
        results.sort(key=lambda m: m.period_start, reverse=True)
        return results[:limit]

    async def find_latest(
        self,
        session_id: uuid4,
        metric_name: str,
    ) -> LiftMeasurement | None:
        results = [
            m for m in self.measurements.values()
            if m.shadow_session_id == session_id and m.metric_name == metric_name
        ]
        if not results:
            return None
        return max(results, key=lambda m: m.created_at)


# --- Fixtures ---

@pytest.fixture
def session_repo():
    return MockSessionRepository()

@pytest.fixture
def decision_repo():
    return MockDecisionRepository()

@pytest.fixture
def event_repo():
    return MockEventRepository()

@pytest.fixture
def lift_repo():
    return MockLiftRepository()

@pytest.fixture
def session_service(session_repo, decision_repo, event_repo):
    return ShadowSessionService(session_repo, decision_repo, event_repo)

@pytest.fixture
def decision_service(session_repo, decision_repo, event_repo):
    return ShadowDecisionService(session_repo, decision_repo, event_repo)

@pytest.fixture
def lift_service(decision_repo):
    # We need a lift repo too
    class MockLiftRepo:
        def __init__(self):
            self.measurements = {}
        async def save(self, m):
            self.measurements[m.id] = m
            return m
        async def find_by_session(self, session_id, limit=50):
            return list(self.measurements.values())[:limit]
        async def find_latest(self, session_id, metric_name):
            return None
    lift_repo = MockLiftRepo()
    session_repo_for_lift = MockSessionRepository()
    decision_repo_for_lift = MockDecisionRepository()
    return LiftMeasurementService(lift_repo, decision_repo, session_repo_for_lift)

# --- Entity Tests ---

class TestShadowSession:
    def test_create_session(self):
        session = ShadowSession(
            organization_id=uuid4(),
            name="Test Session",
            agent_type="CampaignOptimizer",
            agent_model="gpt-4",
            decision_types=[
                DecisionType.BUDGET_ADJUSTMENT,
                DecisionType.BID_OPTIMIZATION,
            ],
            created_by=uuid4(),
        )
        assert session.name == "Test Session"
        assert session.agent_type == "CampaignOptimizer"
        assert session.status == ShadowModeStatus.ENABLED
        assert session.require_human_approval is True

    def test_agreement_rate(self):
        session = ShadowSession(
            organization_id=uuid4(),
            total_decisions=100,
            agreements=75,
        )
        assert session.agreement_rate() == 0.75

    def test_human_override_rate(self):
        session = ShadowSession(
            organization_id=uuid4(),
            agent_decisions=100,
            human_overrides=20,
        )
        assert session.human_override_rate() == 0.20

    def test_is_healthy(self):
        session = ShadowSession(
            organization_id=uuid4(),
            total_decisions=50,
            agreements=35,
            agent_decisions=40,
            human_overrides=10,
            agreement_threshold=0.7,
            max_human_override_rate=0.3,
            min_decisions_for_comparison=10,
        )
        assert session.is_healthy() is True

    def test_is_healthy_low_agreement(self):
        session = ShadowSession(
            organization_id=uuid4(),
            total_decisions=50,
            agreements=20,
            agent_decisions=40,
            human_overrides=10,
            agreement_threshold=0.7,
            max_human_override_rate=0.3,
            min_decisions_for_comparison=10,
        )
        assert session.is_healthy() is False

    def test_to_dict(self):
        session = ShadowSession(
            organization_id=uuid4(),
            name="Test",
        )
        d = session.to_dict()
        assert d["name"] == "Test"
        assert d["status"] == "enabled"


class TestShadowDecision:
    def test_create_decision(self):
        decision = ShadowDecision(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            decision_type=DecisionType.BID_OPTIMIZATION,
            entity_id="campaign-123",
            entity_type="campaign",
            agent_decision={"action": "increase_bid", "amount": 1.5},
            agent_confidence=0.85,
            agent_reasoning="Strong performance signals",
            agent_model="gpt-4",
        )
        assert decision.decision_type == DecisionType.BID_OPTIMIZATION
        assert decision.agent_confidence == 0.85

    def test_has_human_decision(self):
        decision = ShadowDecision(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            decision_type=DecisionType.BUDGET_ADJUSTMENT,
        )
        assert decision.has_human_decision() is False

        decision.human_decision = {"action": "approve"}
        assert decision.has_human_decision() is True

    def test_can_compare(self):
        decision = ShadowDecision(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            decision_type=DecisionType.TARGETING_CHANGE,
        )
        assert decision.can_compare() is False

        decision.human_decision = {"action": "apply"}
        decision.agent_confidence = 0.8
        assert decision.can_compare() is True


class TestComparisonResult:
    def test_comparison_result_values(self):
        assert ComparisonResult.AGREED.value == "agreed"
        assert ComparisonResult.AGENT_BETTER.value == "agent_better"
        assert ComparisonResult.HUMAN_BETTER.value == "human_better"
        assert ComparisonResult.DIFFERENT.value == "different"
        assert ComparisonResult.CONFLICT.value == "conflict"


class TestLiftMeasurement:
    def test_lift_calculation(self):
        measurement = LiftMeasurement(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            metric_name="roas",
            baseline_value=3.0,
            agent_value=4.5,
        )
        assert measurement.lift_percentage == 50.0

    def test_negative_lift(self):
        measurement = LiftMeasurement(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            metric_name="cpa",
            baseline_value=100.0,
            agent_value=120.0,
        )
        assert measurement.lift_percentage == 20.0  # Worse (higher CPA)

    def test_zero_baseline(self):
        measurement = LiftMeasurement(
            organization_id=uuid4(),
            shadow_session_id=uuid4(),
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            metric_name="new_metric",
            baseline_value=0.0,
            agent_value=10.0,
        )
        assert measurement.lift_percentage == 0.0


# --- Service Tests ---

class TestShadowSessionService:
    @pytest.mark.asyncio
    async def test_create_session(self, session_service):
        org_id = uuid4()
        user_id = uuid4()

        session = await session_service.create_session(
            organization_id=org_id,
            name="Test Session",
            description="Test description",
            agent_type="CampaignOptimizer",
            agent_model="gpt-4",
            created_by=user_id,
            campaigns=[uuid4()],
            decision_types=[DecisionType.BUDGET_ADJUSTMENT],
            reviewers=[uuid4()],
        )

        assert session.name == "Test Session"
        assert session.agent_type == "CampaignOptimizer"
        assert session.status == ShadowModeStatus.ENABLED
        assert session.require_human_approval is True

    @pytest.mark.asyncio
    async def test_start_session(self, session_service, session_repo):
        org_id = uuid4()
        user_id = uuid4()

        session = await session_service.create_session(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
        )

        started = await session_service.start_session(session.id, user_id)
        assert started.status == ShadowModeStatus.ENABLED
        assert started.started_at is not None

    @pytest.mark.asyncio
    async def test_pause_session(self, session_service, session_repo):
        org_id = uuid4()
        user_id = uuid4()

        session = await session_service.create_session(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
        )
        await session_service.start_session(session.id, user_id)

        paused = await session_service.pause_session(session.id, user_id)
        assert paused.status == ShadowModeStatus.PAUSED

    @pytest.mark.asyncio
    async def test_end_session(self, session_service):
        org_id = uuid4()
        user_id = uuid4()

        session = await session_service.create_session(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
        )
        await session_service.start_session(session.id, user_id)

        ended = await session_service.end_session(session.id, user_id)
        assert ended.status == ShadowModeStatus.DISABLED
        assert ended.ended_at is not None

    @pytest.mark.asyncio
    async def test_get_session_stats(self, session_service, decision_repo):
        org_id = uuid4()
        user_id = uuid4()

        session = await session_service.create_session(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
        )
        await session_service.start_session(session.id, user_id)

        # Add some decisions
        from app.domain.entities.shadow_mode import DecisionType, ShadowDecision
        for i in range(10):
            decision = ShadowDecision(
                organization_id=org_id,
                shadow_session_id=session.id,
                decision_type=DecisionType.BUDGET_ADJUSTMENT,
                entity_id=f"entity-{i}",
                entity_type="campaign",
                agent_decision={"amount": 100 + i},
                agent_confidence=0.8,
            )
            if i < 5:
                decision.human_decision = {"approved": True}
                decision.comparison_result = ComparisonResult.AGREED
                decision.compared_at = datetime.now()
            elif i < 8:
                decision.human_decision = {"approved": False}
                decision.comparison_result = ComparisonResult.DIFFERENT
                decision.compared_at = datetime.now()
            await decision_repo.save(decision)

        stats = await session_service.get_session_stats(session.id)
        assert stats["total_decisions"] == 10
        assert stats["agreements"] == 5
        assert stats["disagreements"] == 3
        assert stats["agreement_rate"] == 0.5


class TestShadowDecisionService:
    @pytest.mark.asyncio
    async def test_record_agent_decision(self, decision_service, session_repo):
        org_id = uuid4()
        user_id = uuid4()
        session = ShadowSession(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
            status=ShadowModeStatus.ENABLED,
        )
        await session_repo.save(session)

        decision = await decision_service.record_agent_decision(
            session_id=session.id,
            decision_type=DecisionType.BID_OPTIMIZATION,
            context={"campaign": "summer-sale"},
            entity_id="campaign-123",
            entity_type="campaign",
            agent_decision={"action": "increase_bid", "bid_amount": 2.50},
            agent_confidence=0.9,
            agent_reasoning="Strong conversion signals",
            agent_model="gpt-4",
        )

        assert decision.agent_confidence == 0.9
        assert decision.decision_type == DecisionType.BID_OPTIMIZATION

    @pytest.mark.asyncio
    async def test_record_human_decision_agreed(self, decision_service, session_repo):
        org_id = uuid4()
        user_id = uuid4()
        session = ShadowSession(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
            status=ShadowModeStatus.ENABLED,
        )
        await session_repo.save(session)

        # Record agent decision
        decision = await decision_service.record_agent_decision(
            session_id=session.id,
            decision_type=DecisionType.BUDGET_ADJUSTMENT,
            context={},
            entity_id="budget-1",
            entity_type="budget",
            agent_decision={"amount": 5000},
            agent_confidence=0.85,
            agent_reasoning="Good ROAS",
            agent_model="gpt-4",
        )

        # Record human decision that agrees
        updated = await decision_service.record_human_decision(
            decision_id=decision.id,
            human_decision={"amount": 5000},
            human_confidence=0.9,
            human_reasoning="Agreed with agent",
            decided_by=user_id,
        )

        assert updated.comparison_result == ComparisonResult.AGREED

    @pytest.mark.asyncio
    async def test_record_human_decision_conflict(self, decision_service, session_repo):
        org_id = uuid4()
        user_id = uuid4()
        session = ShadowSession(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
            status=ShadowModeStatus.ENABLED,
        )
        await session_repo.save(session)

        decision = await decision_service.record_agent_decision(
            session_id=session.id,
            decision_type=DecisionType.BID_OPTIMIZATION,
            context={},
            entity_id="bid-1",
            entity_type="ad_set",
            agent_decision={"bid": 10.0},
            agent_confidence=0.7,
            agent_reasoning="Test",
            agent_model="gpt-4",
        )

        # Human disagrees
        updated = await decision_service.record_human_decision(
            decision_id=decision.id,
            human_decision={"bid": 5.0},
            human_confidence=0.8,
            human_reasoning="Too aggressive",
            decided_by=user_id,
        )

        assert updated.comparison_result in (ComparisonResult.CONFLICT, ComparisonResult.DIFFERENT)

    @pytest.mark.asyncio
    async def test_get_pending_comparisons(self, decision_service, decision_repo, session_repo):
        org_id = uuid4()
        user_id = uuid4()
        session = ShadowSession(
            organization_id=org_id,
            name="Test",
            agent_type="TestAgent",
            agent_model="test",
            created_by=user_id,
        )
        await session_repo.save(session)

        # Add decisions with and without human decisions
        for i in range(5):
            decision = ShadowDecision(
                organization_id=org_id,
                shadow_session_id=session.id,
                decision_type=DecisionType.BUDGET_ADJUSTMENT,
                entity_id=f"entity-{i}",
                entity_type="budget",
                agent_decision={"amount": 100 * i},
                agent_confidence=0.8,
            )
            if i >= 3:
                decision.human_decision = {"approved": True}
                decision.comparison_result = ComparisonResult.AGREED
                decision.compared_at = datetime.now()
            await decision_repo.save(decision)

        pending = await decision_service.get_pending_comparisons(session.id)
        assert len(pending) == 3  # First 3 have no human decision


class TestLiftMeasurementService:
    @pytest.mark.asyncio
    async def test_calculate_lift(self, lift_service):
        session_id = uuid4()
        org_id = uuid4()

        measurement = await lift_service.calculate_lift(
            session_id=session_id,
            metric_name="roas",
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            baseline_value=3.0,
            agent_value=4.5,
            campaigns=[uuid4(), uuid4()],
            decision_types=[DecisionType.BID_OPTIMIZATION],
        )

        assert measurement.metric_name == "roas"
        assert measurement.baseline_value == 3.0
        assert measurement.agent_value == 4.5
        assert measurement.lift_percentage == 50.0

    @pytest.mark.asyncio
    async def test_calculate_lift_zero_baseline(self, lift_service):
        session_id = uuid4()

        measurement = await lift_service.calculate_lift(
            session_id=session_id,
            metric_name="new_metric",
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            baseline_value=0.0,
            agent_value=5.0,
        )

        assert measurement.lift_percentage == 0.0

    @pytest.mark.asyncio
    async def test_get_session_lift_summary(self, lift_service, lift_repo):
        session_id = uuid4()

        # Add some measurements
        for i in range(5):
            m = LiftMeasurement(
                organization_id=uuid4(),
                shadow_session_id=session_id,
                period_start=datetime.now() - timedelta(days=7),
                period_end=datetime.now(),
                metric_name=f"metric_{i}",
                baseline_value=10.0 + i,
                agent_value=12.0 + i,
                is_significant=(i % 2 == 0),
            )
            await lift_repo.save(m)

        summary = await lift_service.get_session_lift_summary(session_id)
        assert summary["measurements"] == 5
        assert summary["significant_lifts"] == 3


class TestShadowModeEntitiesIntegration:
    @pytest.mark.asyncio
    async def test_full_shadow_cycle(self, session_repo, decision_repo, event_repo):
        """Test a complete shadow mode cycle."""
        org_id = uuid4()
        user_id = uuid4()

        session_service = ShadowSessionService(session_repo, decision_repo, event_repo)
        decision_service = ShadowDecisionService(session_repo, decision_repo, event_repo)

        # 1. Create session
        session = await session_service.create_session(
            organization_id=uuid4(),
            name="Campaign Optimization Shadow",
            description="Test shadow mode for campaign optimization",
            agent_type="CampaignOptimizer",
            agent_model="gpt-4",
            created_by=user_id,
            campaigns=[uuid4()],
            decision_types=[DecisionType.BID_OPTIMIZATION, DecisionType.BUDGET_ADJUSTMENT],
        )
        await session_service.start_session(session.id, user_id)

        # 2. Record agent decisions
        for i in range(3):
            await decision_service.record_agent_decision(
                session_id=session.id,
                decision_type=DecisionType.BID_OPTIMIZATION,
                context={"campaign_id": f"campaign-{i}"},
                entity_id=f"campaign-{i}",
                entity_type="campaign",
                agent_decision={"action": "increase_bid", "new_bid": 2.5 + i * 0.5},
                agent_confidence=0.85 + i * 0.05,
                agent_reasoning="Strong conversion rate trend",
                agent_model="gpt-4",
            )

        # 3. Human reviews and agrees with 2, disagrees with 1
        decisions = await decision_repo.find_by_session(session.id)
        for i, decision in enumerate(decisions[:2]):
            await decision_service.record_human_decision(
                decision_id=decision.id,
                human_decision=decision.agent_decision,
                human_confidence=0.9,
                human_reasoning="Agreed with agent assessment",
                decided_by=user_id,
            )

        # Third decision - human disagrees
        third = decisions[2]
        await decision_service.record_human_decision(
            decision_id=third.id,
            human_decision={"action": "maintain_bid", "reason": "Budget constraint"},
            human_confidence=0.8,
            human_reasoning="Budget constraints prevent increase",
            decided_by=user_id,
        )

        # 4. Check stats
        stats = await session_service.get_session_stats(session.id)
        assert stats["total_decisions"] == 3
        assert stats["agreements"] == 2
        assert stats["disagreements"] == 1
        assert stats["human_overrides"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
