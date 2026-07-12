"""Shadow Mode Services — E6.2 Beta Launch.

Services for running agents in shadow mode, comparing decisions with humans,
and measuring lift to build confidence before autonomous operation.
"""

from __future__ import annotations

import logging
import statistics
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
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
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus

logger = logging.getLogger(__name__)


# --- Repository Interfaces ---

class ShadowSessionRepository:
    async def save(self, session: ShadowSession) -> ShadowSession: ...
    async def find_by_id(self, session_id: UUID) -> ShadowSession | None: ...
    async def find_by_organization(
        self,
        org_id: UUID,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]: ...
    async def list_all(
        self,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]: ...


class ShadowDecisionRepository:
    async def save(self, decision: ShadowDecision) -> ShadowDecision: ...
    async def find_by_id(self, decision_id: UUID) -> ShadowDecision | None: ...
    async def find_by_session(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> list[ShadowDecision]: ...
    async def find_pending_comparison(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> list[ShadowDecision]: ...
    async def find_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 10,
    ) -> list[ShadowDecision]: ...


class ShadowEventRepository:
    async def save(self, event: ShadowEvent) -> ShadowEvent: ...
    async def find_by_session(
        self,
        session_id: UUID,
        event_type: ShadowEventType | None = None,
        limit: int = 100,
    ) -> list[ShadowEvent]: ...


class LiftMeasurementRepository:
    async def save(self, measurement: LiftMeasurement) -> LiftMeasurement: ...
    async def find_by_session(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> list[LiftMeasurement]: ...
    async def find_latest(
        self,
        session_id: UUID,
        metric_name: str,
    ) -> LiftMeasurement | None: ...


# --- Shadow Session Service ---

class ShadowSessionService:
    """Manages shadow mode sessions lifecycle."""

    def __init__(
        self,
        session_repo: ShadowSessionRepository,
        decision_repo: ShadowDecisionRepository,
        event_repo: ShadowEventRepository,
    ) -> None:
        self.session_repo = session_repo
        self.decision_repo = decision_repo
        self.event_repo = event_repo

    async def create_session(
        self,
        organization_id: UUID,
        name: str,
        description: str,
        agent_type: str,
        agent_model: str,
        created_by: UUID,
        campaigns: list[UUID] | None = None,
        ad_accounts: list[str] | None = None,
        decision_types: list[DecisionType] | None = None,
        reviewers: list[UUID] | None = None,
        require_human_approval: bool = True,
        auto_approve_threshold: float = 0.9,
        agreement_threshold: float = 0.7,
        lift_threshold: float = 0.05,
        max_human_override_rate: float = 0.3,
        schedule_cron: str | None = None,
    ) -> ShadowSession:
        session = ShadowSession(
            organization_id=organization_id,
            name=name,
            description=description,
            agent_type=agent_type,
            agent_model=agent_model,
            campaigns=campaigns or [],
            ad_accounts=ad_accounts or [],
            decision_types=decision_types or [
                DecisionType.BUDGET_ADJUSTMENT,
                DecisionType.BID_OPTIMIZATION,
                DecisionType.TARGETING_CHANGE,
            ],
            reviewers=reviewers or [],
            require_human_approval=require_human_approval,
            auto_approve_threshold=auto_approve_threshold,
            agreement_threshold=agreement_threshold,
            lift_threshold=lift_threshold,
            max_human_override_rate=max_human_override_rate,
            schedule_cron=schedule_cron,
            created_by=created_by,
        )
        saved = await self.session_repo.save(session)

        await self._log_event(
            session_id=saved.id,
            organization_id=organization_id,
            event_type=ShadowEventType.DECISION_MADE,
            description=f"Shadow session '{name}' created",
            actor_type="human",
            actor_id=created_by,
        )

        return saved

    async def start_session(self, session_id: UUID, started_by: UUID) -> ShadowSession:
        session = await self.session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Shadow session {session_id} not found")

        if session.status != ShadowModeStatus.ENABLED:
            raise ValueError(f"Session is not in enabled status: {session.status.value}")

        session.status = ShadowModeStatus.ENABLED
        session.started_at = now()
        session.updated_at = now()
        saved = await self.session_repo.save(session)

        await self._log_event(
            session_id=session_id,
            organization_id=session.organization_id,
            event_type=ShadowEventType.DECISION_MADE,
            description="Shadow session started",
            actor_type="human",
            actor_id=started_by,
        )

        return saved

    async def pause_session(self, session_id: UUID, paused_by: UUID) -> ShadowSession:
        session = await self.session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Shadow session {session_id} not found")

        session.status = ShadowModeStatus.PAUSED
        session.updated_at = now()
        saved = await self.session_repo.save(session)

        await self._log_event(
            session_id=session_id,
            organization_id=session.organization_id,
            event_type=ShadowEventType.DECISION_MADE,
            description="Shadow session paused",
            actor_type="human",
            actor_id=paused_by,
        )

        return saved

    async def end_session(self, session_id: UUID, ended_by: UUID) -> ShadowSession:
        session = await self.session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Shadow session {session_id} not found")

        session.status = ShadowModeStatus.ARCHIVED
        session.ended_at = now()
        session.updated_at = now()
        saved = await self.session_repo.save(session)

        await self._log_event(
            session_id=session_id,
            organization_id=session.organization_id,
            event_type=ShadowEventType.DECISION_MADE,
            description="Shadow session ended",
            actor_type="human",
            actor_id=ended_by,
        )

        return saved

    async def get_session(self, session_id: UUID) -> ShadowSession | None:
        return await self.session_repo.find_by_id(session_id)

    async def list_sessions(
        self,
        organization_id: UUID,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]:
        return await self.session_repo.find_by_organization(organization_id, status, limit)

    async def get_session_stats(self, session_id: UUID) -> dict[str, Any]:
        session = await self.session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Shadow session {session_id} not found")

        decisions = await self.decision_repo.find_by_session(session_id)

        total = len(decisions)
        with_human = [d for d in decisions if d.has_human_decision()]
        agreements = [d for d in with_human if d.comparison_result == ComparisonResult.AGREED]
        disagreements = [d for d in with_human if d.comparison_result == ComparisonResult.DIFFERENT]
        agent_better = [d for d in with_human if d.comparison_result == ComparisonResult.AGENT_BETTER]
        human_better = [d for d in with_human if d.comparison_result == ComparisonResult.HUMAN_BETTER]
        overrides = [d for d in decisions if d.human_decision and d.comparison_result != ComparisonResult.AGREED]

        return {
            "session": session.to_dict(),
            "total_decisions": total,
            "agent_decisions": len(decisions),
            "human_decisions": len(with_human),
            "pending_comparison": total - len(with_human),
            "agreements": len(agreements),
            "disagreements": len(disagreements),
            "agent_better": len(agent_better),
            "human_better": len(human_better),
            "agreement_rate": len(agreements) / len(with_human) if with_human else 0,
            "human_overrides": len(overrides),
            "override_rate": len(overrides) / len(decisions) if decisions else 0,
        }

    async def _log_event(
        self,
        session_id: UUID,
        organization_id: UUID,
        event_type: ShadowEventType,
        description: str,
        actor_type: str,
        actor_id: UUID | None = None,
        severity: str = "info",
    ) -> None:
        event = ShadowEvent(
            organization_id=organization_id,
            shadow_session_id=session_id,
            event_type=event_type,
            description=description,
            actor_type=actor_type,
            actor_id=actor_id,
            severity=severity,
        )
        await self.event_repo.save(event)


# --- Shadow Decision Service ---

class ShadowDecisionService:
    """Manages shadow decisions - recording, comparison, and tracking."""

    def __init__(
        self,
        session_repo: ShadowSessionRepository,
        decision_repo: ShadowDecisionRepository,
        event_repo: ShadowEventRepository,
    ) -> None:
        self.session_repo = session_repo
        self.decision_repo = decision_repo
        self.event_repo = event_repo

    async def record_agent_decision(
        self,
        session_id: UUID,
        decision_type: DecisionType,
        context: dict[str, Any],
        entity_id: str,
        entity_type: str,
        agent_decision: dict[str, Any],
        agent_confidence: float,
        agent_reasoning: str,
        agent_model: str,
    ) -> ShadowDecision:
        """Record an agent's decision in shadow mode."""
        session = await self.session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Shadow session {session_id} not found")

        if session.status != ShadowModeStatus.ENABLED:
            raise ValueError(f"Session is not active: {session.status.value}")

        if decision_type not in session.decision_types:
            raise ValueError(f"Decision type {decision_type.value} not in session scope")

        decision = ShadowDecision(
            organization_id=session.organization_id,
            shadow_session_id=session_id,
            decision_type=decision_type,
            context=context,
            entity_id=entity_id,
            entity_type=entity_type,
            agent_decision=agent_decision,
            agent_confidence=agent_confidence,
            agent_reasoning=agent_reasoning,
            agent_model=agent_model,
        )

        # Auto-approve if high confidence
        if (
            session.auto_approve_threshold > 0
            and agent_confidence >= session.auto_approve_threshold
            and not session.require_human_approval
        ):
            decision.human_decision = agent_decision
            decision.human_confidence = agent_confidence
            decision.human_reasoning = "Auto-approved: high confidence"
            decision.comparison_result = ComparisonResult.AGREED
            decision.compared_at = now()
            decision.compared_by = uuid4()  # System

        saved = await self.decision_repo.save(decision)

        # Update session stats
        session.total_decisions += 1
        session.agent_decisions += 1
        session.updated_at = now()
        await self.session_repo.save(session)

        await self._log_event(
            session_id=session_id,
            organization_id=session.organization_id,
            event_type=ShadowEventType.DECISION_MADE,
            description=f"Agent decision recorded: {decision_type.value}",
            actor_type="agent",
            actor_id=uuid4(),
            data={"decision_id": str(saved.id), "confidence": agent_confidence},
        )

        return saved

    async def record_human_decision(
        self,
        decision_id: UUID,
        human_decision: dict[str, Any],
        human_confidence: float,
        human_reasoning: str,
        decided_by: UUID,
    ) -> ShadowDecision:
        decision = await self.decision_repo.find_by_id(decision_id)
        if not decision:
            raise ValueError(f"Shadow decision {decision_id} not found")

        decision.human_decision = human_decision
        decision.human_confidence = human_confidence
        decision.human_reasoning = human_reasoning
        decision.decided_by = decided_by

        # Compare decisions
        comparison = self._compare_decisions(
            decision.agent_decision,
            human_decision,
        )
        decision.comparison_result = comparison
        decision.compared_at = now()
        decision.compared_by = decided_by

        # Update session stats
        session = await self.session_repo.find_by_id(decision.shadow_session_id)
        if session:
            session.human_decisions += 1
            if comparison == ComparisonResult.AGREED:
                session.agreements += 1
            elif comparison != ComparisonResult.AGREED:
                session.disagreements += 1
            if comparison != ComparisonResult.AGREED:
                session.human_overrides += 1
            elif comparison == ComparisonResult.AGENT_BETTER:
                session.agent_corrections += 1
            session.updated_at = now()
            await self.session_repo.save(session)

        saved = await self.decision_repo.save(decision)

        await self._log_event(
            session_id=decision.shadow_session_id,
            organization_id=decision.organization_id,
            event_type=ShadowEventType.DECISION_COMPARED,
            description=f"Human decision recorded, comparison: {comparison.value}",
            actor_type="human",
            actor_id=decided_by,
            data={"decision_id": str(decision_id), "comparison": comparison.value},
        )

        return saved

    async def get_decision(self, decision_id: UUID) -> ShadowDecision | None:
        return await self.decision_repo.find_by_id(decision_id)

    async def list_decisions(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> list[ShadowDecision]:
        return await self.decision_repo.find_by_session(session_id, limit)

    async def get_pending_comparisons(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> list[ShadowDecision]:
        return await self.decision_repo.find_pending_comparison(session_id, limit)

    def _compare_decisions(
        self,
        agent_decision: dict[str, Any],
        human_decision: dict[str, Any],
    ) -> ComparisonResult:
        """Compare agent and human decisions."""
        # Simple comparison - in production, this would be more sophisticated
        if agent_decision == human_decision:
            return ComparisonResult.AGREED

        # For budget/bid decisions, compare numeric values
        if "amount" in agent_decision and "amount" in human_decision:
            agent_amt = agent_decision.get("amount", 0)
            human_amt = human_decision.get("amount", 0)
            diff_pct = abs(agent_amt - human_amt) / max(human_amt, 1)
            if diff_pct < 0.1:  # Within 10%
                return ComparisonResult.AGREED

        # Check if agent decision would have been better (would need outcome data)
        # For now, mark as different
        return ComparisonResult.DIFFERENT

    async def _log_event(
        self,
        session_id: UUID,
        organization_id: UUID,
        event_type: ShadowEventType,
        description: str,
        actor_type: str,
        actor_id: UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        event = ShadowEvent(
            organization_id=organization_id,
            shadow_session_id=session_id,
            event_type=event_type,
            description=description,
            actor_type=actor_type,
            actor_id=actor_id,
            data=data or {},
        )
        from app.domain.events.event_bus import EventBus
        await EventBus.publish(event)


# --- Lift Measurement Service ---

class LiftMeasurementService:
    """Calculates and tracks lift measurements for shadow sessions."""

    def __init__(
        self,
        lift_repo: LiftMeasurementRepository,
        decision_repo: ShadowDecisionRepository,
    ) -> None:
        self.lift_repo = lift_repo
        self.decision_repo = decision_repo

    async def calculate_lift(
        self,
        session_id: UUID,
        metric_name: str,
        period_start: datetime,
        period_end: datetime,
        baseline_value: float,
        agent_value: float,
        campaigns: list[UUID] | None = None,
        decision_types: list[DecisionType] | None = None,
    ) -> LiftMeasurement:
        """Calculate lift measurement for a period."""
        if baseline_value == 0:
            lift_pct = 0.0
        else:
            lift_pct = (agent_value - baseline_value) / baseline_value * 100

        measurement = LiftMeasurement(
            organization_id=uuid4(),  # Would come from session
            shadow_session_id=session_id,
            period_start=period_start,
            period_end=period_end,
            metric_name=metric_name,
            baseline_value=baseline_value,
            agent_value=agent_value,
            lift_percentage=lift_pct,
            campaigns=campaigns or [],
            decision_types=decision_types or [],
        )

        # Calculate statistical significance if we have enough data
        if campaigns and len(campaigns) >= 10:
            # Simplified significance test
            # In production, use proper statistical test
            sample_size = len(campaigns)
            # Simplified - assume significant if lift > 5% and sample > 30
            if sample_size >= 30 and abs(lift_pct) > 5:
                measurement.is_significant = True
                measurement.p_value = 0.05
                measurement.confidence_interval = (
                    lift_pct - 5,
                    lift_pct + 5,
                )
            measurement.sample_size = sample_size

        return await self.lift_repo.save(measurement)

    async def get_session_lift_summary(self, session_id: UUID) -> dict[str, Any]:
        measurements = await self.lift_repo.find_by_session(session_id)
        if not measurements:
            return {"measurements": 0, "avg_lift": 0, "significant_lifts": 0}

        avg_lift = statistics.mean(m.lift_percentage for m in measurements)
        significant = [m for m in measurements if m.is_significant]
        positive = [m for m in measurements if m.lift_percentage > 0]

        return {
            "measurements": len(measurements),
            "avg_lift": round(avg_lift, 2),
            "significant_lifts": len(significant),
            "positive_lifts": len(positive),
            "best_lift": max(m.lift_percentage for m in measurements),
            "worst_lift": min(m.lift_percentage for m in measurements),
            "metrics": list(set(m.metric_name for m in measurements)),
        }

    async def record_outcome(
        self,
        decision_id: UUID,
        outcome: dict[str, Any],
        recorded_by: UUID,
    ) -> ShadowDecision:
        decision = await self.decision_repo.find_by_id(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        decision.outcome = outcome
        decision.outcome_recorded_at = now()

        # Calculate lift if we have human decision for comparison
        if decision.has_human_decision() and decision.human_decision:
            # Would calculate actual lift based on outcome metrics
            pass

        return await self.decision_repo.save(decision)