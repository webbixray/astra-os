from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from app.application.use_cases.analytics.advanced_analytics_service import AdvancedAnalyticsService
from app.infrastructure.auth.jwt import JWTService
from app.infrastructure.auth.supabase_jwt import SupabaseJWTVerifier
from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

logger = logging.getLogger(__name__)

router = APIRouter()

_jwt_service = JWTService()
_supabase_verifier = SupabaseJWTVerifier()


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float
    label: str = ""


class TimeSeriesResponse(BaseModel):
    metric: str
    granularity: str
    points: list[TimeSeriesPoint]
    period_start: datetime
    period_end: datetime


class FunnelStage(BaseModel):
    stage: str
    count: int
    conversion_rate: float
    dropoff_rate: float = 0.0


class FunnelResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    stages: list[FunnelStage]
    overall_conversion: float
    period_start: datetime
    period_end: datetime


class ComparativeResponse(BaseModel):
    current_period: dict
    previous_period: dict
    changes: dict
    period_start: datetime
    period_end: datetime
    comparison_type: str


class RevenueAttributionItem(BaseModel):
    source: str
    channel: str
    campaign_id: str | None = None
    campaign_name: str | None = None
    attributed_revenue: float
    attributed_conversions: int
    touchpoint_count: int
    confidence: float


class RevenueAttributionResponse(BaseModel):
    items: list[RevenueAttributionItem]
    total_attributed_revenue: float
    unattributed_revenue: float
    period_start: datetime
    period_end: datetime


class AnalyticsConnectionManager:
    def __init__(self):
        self._connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, organization_id: str):
        await websocket.accept()
        if organization_id not in self._connections:
            self._connections[organization_id] = {}
        self._connections[organization_id][client_id] = websocket
        logger.info("Analytics WebSocket connected: org=%s client=%s", organization_id, client_id)

    def disconnect(self, client_id: str, organization_id: str):
        if organization_id in self._connections:
            self._connections[organization_id].pop(client_id, None)
            if not self._connections[organization_id]:
                del self._connections[organization_id]
        logger.info(
            "Analytics WebSocket disconnected: org=%s client=%s", organization_id, client_id
        )

    async def send_to_organization(self, organization_id: str, data: dict):
        if organization_id in self._connections:
            dead_clients = []
            for client_id, ws in self._connections[organization_id].items():
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_clients.append(client_id)
            for client_id in dead_clients:
                self.disconnect(client_id, organization_id)

    async def broadcast_metric_update(self, organization_id: str, metric_type: str, data: dict):
        payload = {
            "type": "metric_update",
            "metric_type": metric_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        await self.send_to_organization(organization_id, payload)


manager = AnalyticsConnectionManager()


async def _verify_ws_token(token: str) -> UUID | None:
    if _supabase_verifier.enabled:
        payload = await _supabase_verifier.verify_token(token)
        if payload is not None:
            sub = payload.get("sub")
            if sub:
                try:
                    return UUID(sub)
                except ValueError:
                    pass
    payload = _jwt_service.verify_token(token)
    if payload is not None:
        sub = payload.get("sub")
        if sub:
            try:
                return UUID(sub)
            except ValueError:
                pass
    return None


@asynccontextmanager
async def _get_session(websocket: WebSocket) -> AsyncGenerator[AsyncSession, None]:
    session_factory = websocket.app.state.db
    async with session_factory() as session:
        yield session


async def _build_advanced_analytics_service(session: AsyncSession) -> AdvancedAnalyticsService:
    campaign_repo = CampaignRepositoryImpl(session)
    content_repo = ContentRepositoryImpl(session)
    return AdvancedAnalyticsService(campaign_repo, content_repo)


async def _handle_analytics_ws_message(
    websocket: WebSocket,
    client_id: str,
    user_id: UUID,
    session: AsyncSession,
    service: AdvancedAnalyticsService,
    payload: dict,
) -> None:
    action = payload.get("action")

    if action == "subscribe_timeseries":
        metric = payload.get("metric", "overview")
        granularity = payload.get("granularity", "day")
        days = payload.get("days", 30)
        organization_id = payload.get("organization_id")

        if not organization_id:
            await manager.send_json(
                client_id, {"type": "error", "message": "organization_id required"}
            )
            return

        try:
            org_uuid = UUID(organization_id)
            await require_org_role(org_uuid, "viewer", user_id, session)
        except Exception:
            await manager.send_json(client_id, {"type": "error", "message": "Not authorized"})
            return

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        if metric == "overview":
            overview = await service.get_overview(org_uuid)
            await manager.send_json(
                client_id,
                {
                    "type": "timeseries_data",
                    "metric": "overview",
                    "data": overview,
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                },
            )

        asyncio.create_task(
            _stream_timeseries_updates(client_id, org_uuid, metric, granularity, session)
        )

    elif action == "subscribe_funnel":
        campaign_id = payload.get("campaign_id")
        organization_id = payload.get("organization_id")

        if not campaign_id or not organization_id:
            await manager.send_json(
                client_id, {"type": "error", "message": "campaign_id and organization_id required"}
            )
            return

        try:
            org_uuid = UUID(organization_id)
            await require_org_role(org_uuid, "viewer", user_id, session)
        except Exception:
            await manager.send_json(client_id, {"type": "error", "message": "Not authorized"})
            return

        funnel = await service.get_campaign_funnel(UUID(campaign_id))
        await manager.send_json(
            client_id,
            {
                "type": "funnel_data",
                "campaign_id": campaign_id,
                "data": funnel,
            },
        )

    elif action == "subscribe_comparative":
        period_type = payload.get("period_type", "week")
        organization_id = payload.get("organization_id")

        if not organization_id:
            await manager.send_json(
                client_id, {"type": "error", "message": "organization_id required"}
            )
            return

        try:
            org_uuid = UUID(organization_id)
            await require_org_role(org_uuid, "viewer", user_id, session)
        except Exception:
            await manager.send_json(client_id, {"type": "error", "message": "Not authorized"})
            return

        comparative = await service.get_comparative_metrics(org_uuid, period_type)
        await manager.send_json(
            client_id,
            {
                "type": "comparative_data",
                "period_type": period_type,
                "data": comparative,
            },
        )

    elif action == "subscribe_revenue":
        organization_id = payload.get("organization_id")
        days = payload.get("days", 30)

        if not organization_id:
            await manager.send_json(
                client_id, {"type": "error", "message": "organization_id required"}
            )
            return

        try:
            org_uuid = UUID(organization_id)
            await require_org_role(org_uuid, "viewer", user_id, session)
        except Exception:
            await manager.send_json(client_id, {"type": "error", "message": "Not authorized"})
            return

        revenue = await service.get_revenue_attribution(org_uuid, days)
        await manager.send_json(
            client_id,
            {
                "type": "revenue_attribution_data",
                "data": revenue,
            },
        )

    elif action == "ping":
        await manager.send_json(
            client_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        )


async def _stream_timeseries_updates(
    client_id: str,
    organization_id: UUID,
    metric: str,
    granularity: str,
    session: AsyncSession,
):
    """Stream periodic updates for a timeseries metric."""
    try:
        service = await _build_advanced_analytics_service(session)
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            if metric == "overview":
                data = await service.get_overview(organization_id)
                await manager.send_json(
                    client_id,
                    {
                        "type": "timeseries_update",
                        "metric": metric,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Error streaming timeseries updates")


@router.websocket("/ws/analytics")
async def websocket_analytics(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    user_id: UUID | None = None
    if token:
        user_id = await _verify_ws_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Authentication required")
        logger.warning("Analytics WebSocket connection rejected: missing or invalid token")
        return

    client_id = str(user_id)

    org_id_param = websocket.query_params.get("organization_id")
    if not org_id_param:
        await websocket.close(code=4002, reason="organization_id query parameter required")
        return

    try:
        organization_id = UUID(org_id_param)
    except ValueError:
        await websocket.close(code=4003, reason="Invalid organization_id")
        return

    async with _get_session(websocket) as session:
        await require_org_role(organization_id, "viewer", user_id, session)
        service = await _build_advanced_analytics_service(session)

        await manager.connect(websocket, client_id, str(organization_id))

        try:
            await manager.send_json(
                client_id,
                {
                    "type": "connected",
                    "client_id": client_id,
                    "organization_id": str(organization_id),
                    "message": "Connected to Astra OS Analytics streaming",
                },
            )

            while True:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    await manager.send_json(
                        client_id, {"type": "error", "message": "Invalid JSON payload"}
                    )
                    continue

                await _handle_analytics_ws_message(
                    websocket, client_id, user_id, session, service, payload
                )

        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception("Analytics WebSocket error for user %s", user_id)
        finally:
            manager.disconnect(client_id, str(organization_id))


@router.get("/analytics/timeseries", response_model=TimeSeriesResponse)
async def get_timeseries(
    organization_id: UUID,
    metric: str = Query(default="overview", pattern="^(overview|campaigns|content|spend|revenue)$"),
    granularity: str = Query(default="day", pattern="^(hour|day|week|month)$"),
    days: int = Query(default=30, ge=1, le=365),
    service: AdvancedAnalyticsService = Depends(
        lambda db=Depends(get_db): _build_advanced_analytics_service(db)
    ),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    points = await service.get_timeseries(
        organization_id, metric, granularity, start_date, end_date
    )

    return {
        "metric": metric,
        "granularity": granularity,
        "points": points,
        "period_start": start_date,
        "period_end": end_date,
    }


@router.get("/analytics/funnel/{campaign_id}", response_model=FunnelResponse)
async def get_campaign_funnel(
    campaign_id: UUID,
    organization_id: UUID,
    service: AdvancedAnalyticsService = Depends(
        lambda db=Depends(get_db): _build_advanced_analytics_service(db)
    ),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    funnel = await service.get_campaign_funnel(campaign_id)
    return funnel


@router.get("/analytics/comparative", response_model=ComparativeResponse)
async def get_comparative_metrics(
    organization_id: UUID,
    period_type: str = Query(default="week", pattern="^(day|week|month|quarter)$"),
    service: AdvancedAnalyticsService = Depends(
        lambda db=Depends(get_db): _build_advanced_analytics_service(db)
    ),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    comparative = await service.get_comparative_metrics(organization_id, period_type)
    return comparative


@router.get("/analytics/revenue-attribution", response_model=RevenueAttributionResponse)
async def get_revenue_attribution(
    organization_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    service: AdvancedAnalyticsService = Depends(
        lambda db=Depends(get_db): _build_advanced_analytics_service(db)
    ),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    revenue = await service.get_revenue_attribution(organization_id, days)
    return revenue


@router.get("/analytics/realtime")
async def get_realtime_metrics(
    organization_id: UUID,
    service: AdvancedAnalyticsService = Depends(
        lambda db=Depends(get_db): _build_advanced_analytics_service(db)
    ),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current real-time metrics snapshot."""
    await require_org_role(organization_id, "viewer", user_id, db)

    overview = await service.get_overview(organization_id)

    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )

    campaign_repo = CampaignRepositoryImpl(db)
    campaigns = await campaign_repo.find_by_organization(organization_id)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overview": overview,
        "active_campaigns": len([c for c in campaigns if c.status == "active"]),
        "total_campaigns": len(campaigns),
    }
