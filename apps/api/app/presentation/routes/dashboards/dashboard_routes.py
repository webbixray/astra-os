from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.dashboards.dashboard_service import DashboardService
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.db.repositories.dashboards.dashboard_repository import (
    DashboardRepository,
    DashboardWidgetRepository,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateDashboardRequest(BaseModel):
    organization_id: UUID
    name: str
    description: str = ""


class CreateWidgetRequest(BaseModel):
    widget_type: str
    title: str
    pos_x: int = 0
    pos_y: int = 0
    width: int = 1
    height: int = 1
    config: dict = {}


class UpdateWidgetRequest(BaseModel):
    title: str | None = None
    pos_x: int | None = None
    pos_y: int | None = None
    width: int | None = None
    height: int | None = None
    config: dict | None = None


def get_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(
        dash_repo=DashboardRepository(db),
        widget_repo=DashboardWidgetRepository(db),
        db=db,
    )


# ── Dashboard CRUD ───────────────────────────────────────────────────────────

@router.post("/dashboards", status_code=status.HTTP_201_CREATED, summary="Create a new dashboard")
async def create_dashboard(
    request: CreateDashboardRequest,
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    try:
        dash = await service.create_dashboard(
            org_id=request.organization_id,
            name=request.name,
            created_by=user_id,
            description=request.description,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(dash.id), "name": dash.name, "description": dash.description}


@router.get("/dashboards", summary="List all dashboards")
async def list_dashboards(
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_dashboards(org_id=organization_id)


@router.get("/dashboards/{dashboard_id}", summary="Get dashboard by ID")
async def get_dashboard(
    dashboard_id: UUID,
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        return await service.get_dashboard(dashboard_id=dashboard_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found") from None


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a dashboard")
async def delete_dashboard(
    dashboard_id: UUID,
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_dashboard(dashboard_id=dashboard_id)


# ── Widget Management ────────────────────────────────────────────────────────

@router.post("/dashboards/{dashboard_id}/widgets", status_code=status.HTTP_201_CREATED, summary="Add widget to dashboard")
async def add_widget(
    dashboard_id: UUID,
    request: CreateWidgetRequest,
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "member", user_id, db)
    try:
        widget = await service.add_widget(
            dashboard_id=dashboard_id, widget_type=request.widget_type,
            title=request.title, pos_x=request.pos_x, pos_y=request.pos_y,
            width=request.width, height=request.height, config=request.config,
        )
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, EntityNotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    return {
        "id": str(widget.id), "widget_type": widget.widget_type, "title": widget.title,
        "pos_x": widget.pos_x, "pos_y": widget.pos_y,
        "width": widget.width, "height": widget.height, "config": widget.config,
    }


@router.put("/dashboards/widgets/{widget_id}", summary="Update a widget")
async def update_widget(
    widget_id: UUID,
    request: UpdateWidgetRequest,
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "member", user_id, db)
    try:
        widget = await service.update_widget(
            widget_id=widget_id, title=request.title,
            pos_x=request.pos_x, pos_y=request.pos_y,
            width=request.width, height=request.height, config=request.config,
        )
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found") from None
    return {
        "id": str(widget.id), "widget_type": widget.widget_type, "title": widget.title,
        "pos_x": widget.pos_x, "pos_y": widget.pos_y,
        "width": widget.width, "height": widget.height, "config": widget.config,
    }


@router.delete("/dashboards/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a widget")
async def delete_widget(
    widget_id: UUID,
    organization_id: UUID = Query(...),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "member", user_id, db)
    await service.delete_widget(widget_id=widget_id)


# ── Data Queries ─────────────────────────────────────────────────────────────

@router.get("/dashboards/{dashboard_id}/data", summary="Get dashboard data")
async def get_dashboard_data(
    dashboard_id: UUID,
    organization_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.query_dashboard_data(
        dashboard_id=dashboard_id, org_id=organization_id, days=days,
    )


@router.get("/dashboards/metrics/{metric}", summary="Get a single metric")
async def get_metric(
    metric: str,
    organization_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.query_single_metric(
        org_id=organization_id, metric=metric, days=days,
    )


# ── Anomaly Detection & Predictions ──────────────────────────────────────────

@router.get("/dashboards/anomalies/{metric}", summary="Get metric anomalies")
async def get_anomalies(
    metric: str = "ad_spend",
    organization_id: UUID = Query(...),
    days: int = Query(90, ge=7, le=365),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_anomalies(org_id=organization_id, metric=metric, days=days)


@router.get("/dashboards/predictions/{metric}", summary="Get metric predictions")
async def get_predictions(
    metric: str = "ad_spend",
    organization_id: UUID = Query(...),
    periods: int = Query(7, ge=1, le=30),
    service: DashboardService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_prediction(org_id=organization_id, metric=metric, periods=periods)
