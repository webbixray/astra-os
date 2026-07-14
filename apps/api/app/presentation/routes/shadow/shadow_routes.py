"""Shadow Mode API Routes — E6.2 Beta Launch.

Endpoints for shadow mode sessions, decisions, lift measurement, and events.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.shadow_mode import (
    DecisionType,
    ShadowEventType,
    ShadowModeStatus,
)
from app.domain.services.shadow_mode import (
    LiftMeasurementService,
    ShadowDecisionService,
    ShadowEventService,
    ShadowSessionService,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter(prefix="/shadow", tags=["shadow-mode"])


# --- Request/Response Models ---

class ShadowSessionResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str
    status: str
    agent_type: str
    agent_model: str
    campaigns: list[str] = []
    ad_accounts: list[str] = []
    decision_types: list[str] = []
    reviewers: list[str] = []
    require_human_approval: bool
    auto_approve_threshold: float
    agreement_threshold: float
    lift_threshold: float
    max_human_override_rate: float
    schedule_cron: str | None
    started_at: str | None
    ended_at: str | None
    total_decisions: int
    agent_decisions: int
    human_decisions: int
    agreements: int
    disagreements: int
    human_overrides: int
    agent_corrections: int
    avg_lift_vs_baseline: float
    total_lift_measured: int
    created_at: str
    updated_at: str


class SessionStatsResponse(BaseModel):
    total_decisions: int
    agent_decisions: int
    human_decisions: int
    pending_comparison: int
    agreements: int
    disagreements: int
    agent_better: int
    human_better: int
    agreement_rate: float
    human_overrides: int
    override_rate: float


class CreateSessionRequest(BaseModel):
    name: str
    description: str = ""
    agent_type: str
    agent_model: str
    campaigns: list[str] = []
    ad_accounts: list[str] = []
    decision_types: list[str] = []
    reviewers: list[str] = []
    require_human_approval: bool = True
    auto_approve_threshold: float = 0.9
    agreement_threshold: float = 0.7
    lift_threshold: float = 0.05
    max_human_override_rate: float = 0.3
    schedule_cron: str | None = None


class UpdateSessionRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    campaigns: list[str] | None = None
    ad_accounts: list[str] | None = None
    decision_types: list[str] | None = None
    reviewers: list[str] | None = None
    require_human_approval: bool | None = None
    auto_approve_threshold: float | None = None
    agreement_threshold: float | None = None
    lift_threshold: float | None = None
    max_human_override_rate: float | None = None
    schedule_cron: str | None = None


class ShadowDecisionResponse(BaseModel):
    id: str
    organization_id: str
    shadow_session_id: str
    decision_type: str
    context: dict = {}
    entity_id: str
    entity_type: str
    agent_decision: dict = {}
    agent_confidence: float
    agent_reasoning: str = ""
    agent_model: str = ""
    human_decision: dict | None = None
    human_confidence: float | None = None
    human_reasoning: str = ""
    decided_by: str | None = None
    comparison_result: str | None = None
    comparison_notes: str = ""
    compared_at: str | None = None
    compared_by: str | None = None
    outcome: dict | None = None
    outcome_recorded_at: str | None = None
    lift_vs_baseline: float | None = None
    tags: list[str] = []
    created_at: str
    updated_at: str


class RecordAgentDecisionRequest(BaseModel):
    decision_type: str
    context: dict = {}
    entity_id: str
    entity_type: str
    agent_decision: dict
    agent_confidence: float
    agent_reasoning: str = ""
    agent_model: str


class RecordHumanDecisionRequest(BaseModel):
    human_decision: dict
    human_confidence: float
    human_reasoning: str = ""


class RecordOutcomeRequest(BaseModel):
    outcome: dict


class CompareDecisionRequest(BaseModel):
    decision_id: str
    human_decision: dict
    human_confidence: float
    human_reasoning: str = ""


class ShadowEventResponse(BaseModel):
    id: str
    organization_id: str
    shadow_session_id: str
    shadow_decision_id: str | None
    event_type: str
    description: str
    data: dict = {}
    actor_type: str
    actor_id: str | None
    severity: str
    tags: list[str] = []
    created_at: str


class LiftMeasurementResponse(BaseModel):
    id: str
    organization_id: str
    shadow_session_id: str
    period_start: str
    period_end: str
    metric_name: str
    baseline_value: float
    agent_value: float
    lift_percentage: float
    sample_size: int
    p_value: float | None
    confidence_interval: list[float] | None
    is_significant: bool
    decision_types: list[str] = []
    campaigns: list[str] = []
    calculated_at: str
    calculated_by: str | None
    notes: str = ""


class CalculateLiftRequest(BaseModel):
    metric_name: str
    period_start: datetime
    period_end: datetime
    baseline_value: float
    agent_value: float
    campaigns: list[str] = []
    decision_types: list[str] = []


# --- Dependencies ---

async def _require_org_access(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "viewer", user_id, db)
    return organization_id


async def _require_org_admin(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "admin", user_id, db)
    return organization_id


def get_shadow_session_service(db: AsyncSession = Depends(get_db)) -> ShadowSessionService:
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowDecisionRepositoryImpl,
        ShadowEventRepositoryImpl,
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = ShadowDecisionRepositoryImpl(db)
    event_repo = ShadowEventRepositoryImpl(db)
    return ShadowSessionService(session_repo, decision_repo, event_repo)


def get_shadow_decision_service(db: AsyncSession = Depends(get_db)) -> ShadowDecisionService:
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowDecisionRepositoryImpl,
        ShadowEventRepositoryImpl,
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = ShadowDecisionRepositoryImpl(db)
    event_repo = ShadowEventRepositoryImpl(db)
    return ShadowDecisionService(session_repo, decision_repo, event_repo)


def get_lift_measurement_service(db: AsyncSession = Depends(get_db)) -> LiftMeasurementService:
    from app.infrastructure.db.repositories.shadow_repository import (
        LiftMeasurementRepositoryImpl,
        ShadowDecisionRepositoryImpl,
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = ShadowDecisionRepositoryImpl(db)
    measurement_repo = LiftMeasurementRepositoryImpl(db)
    return LiftMeasurementService(measurement_repo, decision_repo, session_repo)


def get_shadow_event_service(db: AsyncSession = Depends(get_db)) -> ShadowEventService:
    from app.infrastructure.db.repositories.shadow_repository import ShadowEventRepositoryImpl
    event_repo = ShadowEventRepositoryImpl(db)
    return ShadowEventService(event_repo)


# --- Session Routes ---

@router.post(
    "/organizations/{organization_id}/sessions",
    response_model=ShadowSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shadow session",
)
async def create_shadow_session(
    organization_id: UUID,
    request: CreateSessionRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowSessionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowDecisionRepositoryImpl,
        ShadowEventRepositoryImpl,
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = ShadowDecisionRepositoryImpl(db)
    event_repo = ShadowEventRepositoryImpl(db)
    service = ShadowSessionService(session_repo, decision_repo, event_repo)

    session = await service.create_session(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        agent_type=request.agent_type,
        agent_model=request.agent_model,
        created_by=user_id,
        campaigns=[UUID(c) for c in request.campaigns] if request.campaigns else None,
        ad_accounts=request.ad_accounts,
        decision_types=[DecisionType(dt) for dt in request.decision_types] if request.decision_types else None,
        reviewers=[UUID(r) for r in request.reviewers] if request.reviewers else None,
        require_human_approval=request.require_human_approval,
        auto_approve_threshold=request.auto_approve_threshold,
        agreement_threshold=request.agreement_threshold,
        lift_threshold=request.lift_threshold,
        max_human_override_rate=request.max_human_override_rate,
        schedule_cron=request.schedule_cron,
    )
    return session.to_dict()


@router.get(
    "/organizations/{organization_id}/sessions",
    response_model=list[ShadowSessionResponse],
    summary="List shadow sessions",
)
async def list_shadow_sessions(
    organization_id: UUID,
    status: str | None = Query(None),
    limit: int = Query(50, le=100),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.domain.services.shadow_mode import ShadowSessionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowSessionService(session_repo(db), decision_repo(db), event_repo(db))

    status_enum = ShadowModeStatus(status) if status else None
    sessions = await service.list_sessions(organization_id, status_enum, limit)
    return [s.to_dict() for s in sessions]


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}",
    response_model=ShadowSessionResponse,
    summary="Get a shadow session",
)
async def get_shadow_session(
    organization_id: UUID,
    session_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.shadow_repository import ShadowSessionRepositoryImpl
    session_repo = ShadowSessionRepositoryImpl(db)
    session = await session_repo.find_by_id(session_id)
    if not session or session.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Shadow session not found")
    return session.to_dict()


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/start",
    response_model=ShadowSessionResponse,
    summary="Start a shadow session",
)
async def start_shadow_session(
    organization_id: UUID,
    session_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    from app.domain.services.shadow_mode import ShadowSessionService
    service = ShadowSessionService(session_repo(db), decision_repo(db), event_repo(db))
    session = await service.start_session(session_id, user_id)
    return session.to_dict()


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/pause",
    response_model=ShadowSessionResponse,
    summary="Pause a shadow session",
)
async def pause_shadow_session(
    organization_id: UUID,
    session_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowSessionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowSessionService(session_repo(db), decision_repo(db), event_repo(db))
    session = await service.pause_session(session_id, user_id)
    return session.to_dict()


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/end",
    response_model=ShadowSessionResponse,
    summary="End a shadow session",
)
async def end_shadow_session(
    organization_id: UUID,
    session_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowSessionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowSessionService(session_repo(db), decision_repo(db), event_repo(db))
    session = await service.end_session(session_id, user_id)
    return session.to_dict()


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/stats",
    response_model=SessionStatsResponse,
    summary="Get shadow session statistics",
)
async def get_session_stats(
    organization_id: UUID,
    session_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowSessionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowSessionService(session_repo(db), decision_repo(db), event_repo(db))
    return await service.get_session_stats(session_id)


# --- Decision Routes ---

@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/decisions/agent",
    response_model=ShadowDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an agent decision",
)
async def record_agent_decision(
    organization_id: UUID,
    session_id: UUID,
    request: RecordAgentDecisionRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    decision = await service.record_agent_decision(
        session_id=session_id,
        decision_type=DecisionType(request.decision_type),
        context=request.context,
        entity_id=request.entity_id,
        entity_type=request.entity_type,
        agent_decision=request.agent_decision,
        agent_confidence=request.agent_confidence,
        agent_reasoning=request.agent_reasoning,
        agent_model=request.agent_model,
    )
    return decision.to_dict()


@router.post(
    "/organizations/{organization_id}/decisions/{decision_id}/human",
    response_model=ShadowDecisionResponse,
    summary="Record human decision for comparison",
)
async def record_human_decision(
    organization_id: UUID,
    decision_id: UUID,
    request: RecordHumanDecisionRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    decision = await service.record_human_decision(
        decision_id=decision_id,
        human_decision=request.human_decision,
        human_confidence=request.human_confidence,
        human_reasoning=request.human_reasoning,
        decided_by=user_id,
    )
    return decision.to_dict()


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/decisions",
    response_model=list[ShadowDecisionResponse],
    summary="List decisions in a session",
)
async def list_decisions(
    organization_id: UUID,
    session_id: UUID,
    limit: int = Query(100, le=200),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    decisions = await service.list_decisions(session_id, limit)
    return [d.to_dict() for d in decisions]


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/decisions/pending",
    response_model=list[ShadowDecisionResponse],
    summary="Get decisions pending human comparison",
)
async def get_pending_comparisons(
    organization_id: UUID,
    session_id: UUID,
    limit: int = Query(50, le=100),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    decisions = await service.get_pending_comparisons(session_id)
    return [d.to_dict() for d in decisions[:limit]]


@router.get(
    "/organizations/{organization_id}/decisions/{decision_id}",
    response_model=ShadowDecisionResponse,
    summary="Get a specific decision",
)
async def get_decision(
    organization_id: UUID,
    decision_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    decision = await decision_repo(db).find_by_id(decision_id)
    if not decision or decision.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision.to_dict()


@router.post(
    "/organizations/{organization_id}/decisions/{decision_id}/outcome",
    response_model=ShadowDecisionResponse,
    summary="Record outcome for a decision",
)
async def record_outcome(
    organization_id: UUID,
    decision_id: UUID,
    request: RecordOutcomeRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    decision = await service.record_outcome(decision_id, request.outcome, user_id)
    return decision.to_dict()


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/decisions/batch-compare",
    summary="Batch record human decisions for pending comparisons",
)
async def batch_compare_decisions(
    organization_id: UUID,
    session_id: UUID,
    comparisons: list[CompareDecisionRequest],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import ShadowDecisionService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    event_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowEventRepositoryImpl"]).ShadowEventRepositoryImpl
    service = ShadowDecisionService(session_repo(db), decision_repo(db), event_repo(db))

    results = []
    for comp in comparisons:
        try:
            decision = await service.record_human_decision(
                decision_id=UUID(comp.decision_id),
                human_decision=comp.human_decision,
                human_confidence=comp.human_confidence,
                human_reasoning=comp.human_reasoning,
                decided_by=user_id,
            )
            results.append({"decision_id": comp.decision_id, "status": "success", "comparison": decision.comparison_result.value})
        except Exception as e:
            results.append({"decision_id": comp.decision_id, "status": "error", "error": str(e)})

    return {"processed": len(comparisons), "results": results}


# --- Lift Measurement Routes ---

@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/lift/calculate",
    response_model=LiftMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate lift measurement for a period",
)
async def calculate_lift(
    organization_id: UUID,
    session_id: UUID,
    request: CalculateLiftRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import LiftMeasurementService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    measurement_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["LiftMeasurementRepositoryImpl"]).LiftMeasurementRepositoryImpl
    service = LiftMeasurementService(measurement_repo(db), decision_repo(db), session_repo(db))

    measurement = await service.calculate_lift(
        session_id=session_id,
        metric_name=request.metric_name,
        period_start=request.period_start,
        period_end=request.period_end,
        calculated_by=user_id,
    )
    return measurement.to_dict()


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/lift",
    response_model=list[LiftMeasurementResponse],
    summary="List lift measurements for a session",
)
async def list_lift_measurements(
    organization_id: UUID,
    session_id: UUID,
    limit: int = Query(50, le=100),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.domain.services.shadow_mode import LiftMeasurementService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    measurement_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["LiftMeasurementRepositoryImpl"]).LiftMeasurementRepositoryImpl
    service = LiftMeasurementService(measurement_repo(db), decision_repo(db), session_repo(db))

    measurements = await service.get_measurements(session_id, limit)
    return [m.to_dict() for m in measurements]


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/lift/summary",
    summary="Get lift summary for a session",
)
async def get_lift_summary(
    organization_id: UUID,
    session_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import LiftMeasurementService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    measurement_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["LiftMeasurementRepositoryImpl"]).LiftMeasurementRepositoryImpl
    service = LiftMeasurementService(measurement_repo(db), decision_repo(db), session_repo(db))

    return await service.get_session_lift_summary(session_id)


# --- Event Routes ---

@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/events",
    response_model=list[ShadowEventResponse],
    summary="Get events for a shadow session",
)
async def get_session_events(
    organization_id: UUID,
    session_id: UUID,
    event_type: str | None = Query(None),
    limit: int = Query(100, le=200),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.domain.services.shadow_mode import ShadowEventService
    from app.infrastructure.db.repositories.shadow_repository import ShadowEventRepositoryImpl
    event_repo = ShadowEventRepositoryImpl(db)
    service = ShadowEventService(event_repo)

    event_type_enum = ShadowEventType(event_type) if event_type else None
    events = await service.get_session_events(session_id, event_type_enum, limit)
    return [e.to_dict() for e in events]


# --- Batch Operations ---

@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/lift/calculate-multiple",
    summary="Calculate lift for multiple metrics",
)
async def calculate_multiple_lifts(
    organization_id: UUID,
    session_id: UUID,
    requests: list[CalculateLiftRequest],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.domain.services.shadow_mode import LiftMeasurementService
    from app.infrastructure.db.repositories.shadow_repository import (
        ShadowSessionRepositoryImpl,
    )
    session_repo = ShadowSessionRepositoryImpl(db)
    decision_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["ShadowDecisionRepositoryImpl"]).ShadowDecisionRepositoryImpl
    measurement_repo = __import__("app.infrastructure.db.repositories.shadow_repository", fromlist=["LiftMeasurementRepositoryImpl"]).LiftMeasurementRepositoryImpl
    service = LiftMeasurementService(measurement_repo(db), decision_repo(db), session_repo(db))

    results = []
    for req in requests:
        try:
            measurement = await service.calculate_lift(
                session_id=session_id,
                metric_name=req.metric_name,
                period_start=req.period_start,
                period_end=req.period_end,
                calculated_by=user_id,
            )
            results.append({"metric": req.metric_name, "status": "success", "lift": measurement.lift_percentage})
        except Exception as e:
            results.append({"metric": req.metric_name, "status": "error", "error": str(e)})

    return {"calculated": len(requests), "results": results}
