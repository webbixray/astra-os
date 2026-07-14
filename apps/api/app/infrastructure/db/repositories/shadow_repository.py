"""Shadow Mode Repository Implementation — E6.2 Beta Launch."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.shadow_mode import (
    DecisionType,
    LiftMeasurement,
    ShadowDecision,
    ShadowEvent,
    ShadowEventType,
    ShadowModeStatus,
    ShadowSession,
)


class ShadowSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model) -> ShadowSession:
        return ShadowSession(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            description=model.description,
            status=ShadowModeStatus(model.status),
            agent_type=model.agent_type,
            agent_model=model.agent_model,
            agent_config=json.loads(model.agent_config) if model.agent_config else {},
            campaigns=[UUID(c) for c in json.loads(model.campaigns) if c] if model.campaigns else [],
            ad_accounts=json.loads(model.ad_accounts) if model.ad_accounts else [],
            decision_types=[DecisionType(dt) for dt in json.loads(model.decision_types) if dt] if model.decision_types else [],
            reviewers=[UUID(r) for r in json.loads(model.reviewers) if r] if model.reviewers else [],
            require_human_approval=model.require_human_approval.lower() == "true",
            auto_approve_threshold=float(model.auto_approve_threshold) if model.auto_approve_threshold else 0.9,
            agreement_threshold=float(model.agreement_threshold) if model.agreement_threshold else 0.7,
            lift_threshold=float(model.lift_threshold) if model.lift_threshold else 0.05,
            max_human_override_rate=float(model.max_human_override_rate) if model.max_human_override_rate else 0.3,
            schedule_cron=model.schedule_cron,
            started_at=model.started_at,
            ended_at=model.ended_at,
            total_decisions=int(model.total_decisions) if model.total_decisions else 0,
            agent_decisions=int(model.agent_decisions) if model.agent_decisions else 0,
            human_decisions=int(model.human_decisions) if model.human_decisions else 0,
            agreements=int(model.agreements) if model.agreements else 0,
            disagreements=int(model.disagreements) if model.disagreements else 0,
            human_overrides=int(model.human_overrides) if model.human_overrides else 0,
            agent_corrections=int(model.agent_corrections) if model.agent_corrections else 0,
            avg_lift_vs_baseline=float(model.avg_lift_vs_baseline) if model.avg_lift_vs_baseline else 0.0,
            total_lift_measured=int(model.total_lift_measured) if model.total_lift_measured else 0,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: ShadowSession) -> dict:
        return {
            "id": entity.id,
            "organization_id": entity.organization_id,
            "name": entity.name,
            "description": entity.description,
            "status": entity.status.value,
            "agent_type": entity.agent_type,
            "agent_model": entity.agent_model,
            "agent_config": json.dumps(entity.agent_config),
            "campaigns": json.dumps([str(c) for c in entity.campaigns]),
            "ad_accounts": json.dumps(entity.ad_accounts),
            "decision_types": json.dumps([dt.value for dt in entity.decision_types]),
            "reviewers": json.dumps([str(r) for r in entity.reviewers]),
            "require_human_approval": str(entity.require_human_approval).lower(),
            "auto_approve_threshold": str(entity.auto_approve_threshold),
            "agreement_threshold": str(entity.agreement_threshold),
            "lift_threshold": str(entity.lift_threshold),
            "max_human_override_rate": str(entity.max_human_override_rate),
            "schedule_cron": entity.schedule_cron,
            "started_at": entity.started_at,
            "ended_at": entity.ended_at,
            "total_decisions": str(entity.total_decisions),
            "agent_decisions": str(entity.agent_decisions),
            "human_decisions": str(entity.human_decisions),
            "agreements": str(entity.agreements),
            "disagreements": str(entity.disagreements),
            "human_overrides": str(entity.human_overrides),
            "agent_corrections": str(entity.agent_corrections),
            "avg_lift_vs_baseline": str(entity.avg_lift_vs_baseline),
            "total_lift_measured": str(entity.total_lift_measured),
            "created_by": entity.created_by,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def save(self, session: ShadowSession) -> ShadowSession:
        model_data = self._entity_to_model(session)
        from app.infrastructure.db.models.shadow import ShadowSessionModel as Model
        existing = await self.db.get(Model, session.id)
        if existing:
            for attr, value in model_data.items():
                setattr(existing, attr, value)
            session_model = existing
        else:
            session_model = Model(**model_data)
            self.db.add(session_model)
        await self.db.flush()
        await self.db.refresh(session_model)
        return self._model_to_entity(session_model)

    async def find_by_id(self, session_id: UUID) -> ShadowSession | None:
        from app.infrastructure.db.models.shadow import ShadowSessionModel as Model
        result = await self.db.execute(select(Model).where(Model.id == session_id))
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def find_by_organization(
        self,
        org_id: UUID,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]:
        from app.infrastructure.db.models.shadow import ShadowSessionModel as Model
        query = select(Model).where(Model.organization_id == org_id)
        if status:
            query = query.where(Model.status == status.value)
        query = query.order_by(Model.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_all(
        self,
        status: ShadowModeStatus | None = None,
        limit: int = 50,
    ) -> list[ShadowSession]:
        from app.infrastructure.db.models.shadow import ShadowSessionModel as Model
        query = select(Model)
        if status:
            query = query.where(Model.status == status.value)
        query = query.order_by(Model.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]


class ShadowDecisionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model) -> ShadowDecision:
        return ShadowDecision(
            id=model.id,
            organization_id=model.organization_id,
            shadow_session_id=model.shadow_session_id,
            decision_type=DecisionType(model.decision_type),
            context=json.loads(model.context) if model.context else {},
            entity_id=model.entity_id,
            entity_type=model.entity_type,
            agent_decision=json.loads(model.agent_decision) if model.agent_decision else {},
            agent_confidence=float(model.agent_confidence) if model.agent_confidence else 0.0,
            agent_reasoning=model.agent_reasoning or "",
            agent_model=model.agent_model or "",
            human_decision=json.loads(model.human_decision) if model.human_decision else None,
            human_confidence=float(model.human_confidence) if model.human_confidence else None,
            human_reasoning=model.human_reasoning or "",
            decided_by=model.decided_by,
            comparison_result=model.comparison_result or None,
            comparison_notes=model.comparison_notes or "",
            compared_at=model.compared_at,
            compared_by=model.compared_by,
            outcome=json.loads(model.outcome) if model.outcome else None,
            outcome_recorded_at=model.outcome_recorded_at,
            lift_vs_baseline=float(model.lift_vs_baseline) if model.lift_vs_baseline else None,
            tags=json.loads(model.tags) if model.tags else [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity) -> dict:
        return {
            "id": entity.id,
            "organization_id": entity.organization_id,
            "shadow_session_id": entity.shadow_session_id,
            "decision_type": entity.decision_type.value,
            "context": json.dumps(entity.context),
            "entity_id": entity.entity_id,
            "entity_type": entity.entity_type,
            "agent_decision": json.dumps(entity.agent_decision),
            "agent_confidence": str(entity.agent_confidence),
            "agent_reasoning": entity.agent_reasoning,
            "agent_model": entity.agent_model,
            "human_decision": json.dumps(entity.human_decision) if entity.human_decision else None,
            "human_confidence": str(entity.human_confidence) if entity.human_confidence else None,
            "human_reasoning": entity.human_reasoning,
            "decided_by": entity.decided_by,
            "comparison_result": entity.comparison_result,
            "comparison_notes": entity.comparison_notes,
            "compared_at": entity.compared_at,
            "compared_by": entity.compared_by,
            "outcome": json.dumps(entity.outcome) if entity.outcome else None,
            "outcome_recorded_at": entity.outcome_recorded_at,
            "lift_vs_baseline": str(entity.lift_vs_baseline) if entity.lift_vs_baseline else None,
            "tags": json.dumps(entity.tags),
        }

    async def save(self, decision) -> ShadowDecision:
        from app.infrastructure.db.models.shadow import ShadowDecisionModel as Model
        model_data = self._entity_to_model(decision)
        existing = await self.db.get(Model, decision.id)
        if existing:
            for attr, value in model_data.items():
                setattr(existing, attr, value)
            session_model = existing
        else:
            session_model = Model(**model_data)
            self.db.add(session_model)
        await self.db.flush()
        await self.db.refresh(session_model)
        return self._model_to_entity(session_model)

    async def find_by_id(self, decision_id: UUID):
        from app.infrastructure.db.models.shadow import ShadowDecisionModel as Model
        result = await self.db.execute(select(Model).where(Model.id == decision_id))
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def find_by_session(self, session_id: UUID, limit: int = 100):
        from app.infrastructure.db.models.shadow import ShadowDecisionModel as Model
        result = await self.db.execute(
            select(Model)
            .where(Model.shadow_session_id == session_id)
            .order_by(Model.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def find_pending_comparison(self, session_id: UUID, limit: int = 50):
        from app.infrastructure.db.models.shadow import ShadowDecisionModel as Model
        result = await self.db.execute(
            select(Model)
            .where(Model.shadow_session_id == session_id)
            .where(Model.human_decision.is_(None))
            .order_by(Model.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def find_by_entity(self, entity_type: str, entity_id: str, limit: int = 10):
        from app.infrastructure.db.models.shadow import ShadowDecisionModel as Model
        result = await self.db.execute(
            select(Model)
            .where(Model.entity_type == entity_type)
            .where(Model.entity_id == entity_id)
            .order_by(Model.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]


class ShadowEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model):
        return ShadowEvent(
            id=model.id,
            organization_id=model.organization_id,
            shadow_session_id=model.shadow_session_id,
            shadow_decision_id=model.shadow_decision_id,
            event_type=ShadowEventType(model.event_type),
            description=model.description or "",
            data=json.loads(model.data) if model.data else {},
            actor_type=model.actor_type or "system",
            actor_id=model.actor_id,
            severity=model.severity or "info",
            tags=json.loads(model.tags) if model.tags else [],
            created_at=model.created_at,
        )

    def _entity_to_model(self, entity):
        return {
            "id": entity.id,
            "organization_id": entity.organization_id,
            "shadow_session_id": entity.shadow_session_id,
            "shadow_decision_id": entity.shadow_decision_id,
            "event_type": entity.event_type.value,
            "description": entity.description,
            "data": json.dumps(entity.data),
            "actor_type": entity.actor_type,
            "actor_id": entity.actor_id,
            "severity": entity.severity,
            "tags": json.dumps(entity.tags),
        }

    async def save(self, event):
        from app.infrastructure.db.models.shadow import ShadowEventModel as Model
        model_data = self._entity_to_model(event)
        model = Model(**model_data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return self._model_to_entity(model)

    async def find_by_session(self, session_id: UUID, event_type=None, limit: int = 100):
        from app.infrastructure.db.models.shadow import ShadowEventModel as Model
        query = select(Model).where(Model.shadow_session_id == session_id)
        if event_type:
            query = query.where(Model.event_type == event_type.value)
        query = query.order_by(Model.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]


class LiftMeasurementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model):
        return LiftMeasurement(
            id=model.id,
            organization_id=model.organization_id,
            shadow_session_id=model.shadow_session_id,
            period_start=model.period_start,
            period_end=model.period_end,
            metric_name=model.metric_name,
            baseline_value=float(model.baseline_value) if model.baseline_value else 0.0,
            agent_value=float(model.agent_value) if model.agent_value else 0.0,
            lift_percentage=float(model.lift_percentage) if model.lift_percentage else 0.0,
            sample_size=int(model.sample_size) if model.sample_size else 0,
            p_value=float(model.p_value) if model.p_value else None,
            confidence_interval=json.loads(model.confidence_interval) if model.confidence_interval else None,
            is_significant=model.is_significant.lower() == "true",
            decision_types=[DecisionType(dt) for dt in json.loads(model.decision_types) if dt] if model.decision_types else [],
            campaigns=[UUID(c) for c in json.loads(model.campaigns) if c] if model.campaigns else [],
            calculated_by=model.calculated_by,
            notes=model.notes or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity):
        return {
            "id": entity.id,
            "organization_id": entity.organization_id,
            "shadow_session_id": entity.shadow_session_id,
            "period_start": entity.period_start,
            "period_end": entity.period_end,
            "metric_name": entity.metric_name,
            "baseline_value": str(entity.baseline_value),
            "agent_value": str(entity.agent_value),
            "lift_percentage": str(entity.lift_percentage),
            "sample_size": str(entity.sample_size),
            "p_value": str(entity.p_value) if entity.p_value else None,
            "confidence_interval": json.dumps(entity.confidence_interval) if entity.confidence_interval else None,
            "is_significant": str(entity.is_significant).lower(),
            "decision_types": json.dumps([dt.value for dt in entity.decision_types]),
            "campaigns": json.dumps([str(c) for c in entity.campaigns]),
            "calculated_by": entity.calculated_by,
            "notes": entity.notes,
        }

    async def save(self, measurement):
        from app.infrastructure.db.models.shadow import LiftMeasurementModel as Model
        model_data = self._entity_to_model(measurement)
        existing = await self.db.get(Model, measurement.id)
        if existing:
            for attr, value in model_data.items():
                setattr(existing, attr, value)
            session_model = existing
        else:
            session_model = Model(**model_data)
            self.db.add(session_model)
        await self.db.flush()
        await self.db.refresh(session_model)
        return self._model_to_entity(session_model)

    async def find_by_session(self, session_id: UUID, limit: int = 50):
        from app.infrastructure.db.models.shadow import LiftMeasurementModel as Model
        result = await self.db.execute(
            select(Model)
            .where(Model.shadow_session_id == session_id)
            .order_by(Model.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def find_latest(self, session_id: UUID, metric_name: str):
        from app.infrastructure.db.models.shadow import LiftMeasurementModel as Model
        result = await self.db.execute(
            select(Model)
            .where(Model.shadow_session_id == session_id)
            .where(Model.metric_name == metric_name)
            .order_by(Model.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
