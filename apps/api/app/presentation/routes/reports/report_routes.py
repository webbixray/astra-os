import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.reports.reporting_service import ReportingService
from app.infrastructure.db.repositories.report_schedule_repository import ReportScheduleRepository
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateScheduleRequest(BaseModel):
    organization_id: UUID
    name: str
    report_type: str = "overview"
    frequency: str = "weekly"
    recipients: list[str] = []
    config: dict = {}


class UpdateScheduleRequest(BaseModel):
    name: str | None = None
    report_type: str | None = None
    frequency: str | None = None
    recipients: list[str] | None = None
    config: dict | None = None
    is_active: bool | None = None


def get_reporting_service(db: AsyncSession = Depends(get_db)) -> ReportingService:
    return ReportingService(db)


@router.get("/reports/overview", summary="Get report overview")
async def get_report_overview(
    organization_id: UUID = Query(...),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    analytics = service.analytics
    return await analytics.get_overview(organization_id)


@router.get("/reports/campaigns", summary="Get campaign report")
async def get_report_campaigns(
    organization_id: UUID = Query(...),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    analytics = service.analytics
    return await analytics.get_campaign_performance(organization_id)


@router.get("/reports/ads", summary="Get ad performance report")
async def get_report_ads(
    organization_id: UUID = Query(...),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    analytics = service.analytics
    return await analytics.get_ad_performance([])


@router.get("/reports/trends", summary="Get metric trends")
async def get_report_trends(
    organization_id: UUID = Query(...),
    metric: str = Query("spend"),
    days: int = Query(30),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_trends(
        organization_id=organization_id,
        metric=metric,
        days=days,
    )


@router.get("/reports/campaigns/timeline", summary="Get campaign timeline")
async def get_campaign_timeline(
    organization_id: UUID = Query(...),
    campaign_ids: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    cids = [UUID(c.strip()) for c in campaign_ids.split(",") if c.strip()]
    return await service.get_campaign_timeline(
        organization_id=organization_id,
        campaign_ids=cids,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/reports/platforms", summary="Get platform comparison")
async def get_platform_comparison(
    organization_id: UUID = Query(...),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_platform_comparison(organization_id)


@router.get("/reports/export/csv", summary="Export report as CSV")
async def export_report_csv(
    type: str = Query(...),
    organization_id: UUID = Query(...),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    service: ReportingService = Depends(get_reporting_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    csv_content = await service.export_csv(
        report_type=type,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '', type)}_report_{datetime.now(UTC).date().isoformat()}.csv"
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/reports/schedules", status_code=201, summary="Create report schedule")
async def create_report_schedule(
    request: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    from app.domain.entities.reports.report_schedule import ReportSchedule

    schedule = ReportSchedule.create(
        organization_id=request.organization_id,
        name=request.name,
        report_type=request.report_type,
        frequency=request.frequency,
        recipients=request.recipients,
        config=request.config,
        created_by=user_id,
    )
    repo = ReportScheduleRepository(db)
    saved = await repo.save(schedule)
    return {
        "id": str(saved.id),
        "name": saved.name,
        "report_type": saved.report_type,
        "frequency": saved.frequency,
        "is_active": saved.is_active,
    }


@router.get("/reports/schedules", summary="List report schedules")
async def list_report_schedules(
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    repo = ReportScheduleRepository(db)
    schedules = await repo.find_by_organization(organization_id)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "report_type": s.report_type,
            "frequency": s.frequency,
            "recipients": s.recipients,
            "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
        }
        for s in schedules
    ]


@router.patch("/reports/schedules/{schedule_id}", summary="Update report schedule")
async def update_report_schedule(
    schedule_id: UUID,
    request: UpdateScheduleRequest,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    await require_org_role(organization_id, "member", user_id, db)
    repo = ReportScheduleRepository(db)
    schedule = await repo.find_by_id(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if str(schedule.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    if request.name is not None:
        schedule.name = request.name
    if request.report_type is not None:
        schedule.report_type = request.report_type
    if request.frequency is not None:
        schedule.frequency = request.frequency
    if request.recipients is not None:
        schedule.recipients = request.recipients
    if request.config is not None:
        schedule.config = request.config
    if request.is_active is not None:
        schedule.is_active = request.is_active
    schedule.updated_at = __import__("datetime").now()
    saved = await repo.save(schedule)
    return {"id": str(saved.id), "is_active": saved.is_active}


@router.delete("/reports/schedules/{schedule_id}", status_code=204, summary="Delete report schedule")
async def delete_report_schedule(
    schedule_id: UUID,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    repo = ReportScheduleRepository(db)
    schedule = await repo.find_by_id(schedule_id)
    if not schedule or str(schedule.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Schedule not found") from None
    await repo.delete(schedule_id)
