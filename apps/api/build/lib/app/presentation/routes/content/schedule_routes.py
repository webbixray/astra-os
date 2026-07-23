"""Content Schedule Routes — API endpoints for managing recurring content schedules."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.content.content_schedule_service import ContentScheduleService
from app.domain.entities.content.content_schedule import ScheduleStatus
from app.infrastructure.db.repositories.content.content_publish_repository import (
    ContentPublishRepository,
)
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl
from app.infrastructure.db.repositories.content.content_schedule_repository import (
    ContentScheduleRepository,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class ScheduleCreateRequest(BaseModel):
    organization_id: UUID
    content_id: UUID
    name: str = Field(min_length=1, max_length=255)
    platform: str
    cron_expression: str
    timezone: str = "UTC"
    max_runs: int | None = None
    metadata: dict = {}


class ScheduleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    cron_expression: str | None = None
    timezone: str | None = None
    max_runs: int | None = None
    metadata: dict | None = None
    status: ScheduleStatus | None = None


class ScheduleResponse(BaseModel):
    id: UUID
    organization_id: UUID
    content_id: UUID
    name: str
    platform: str
    cron_expression: str
    timezone: str
    status: ScheduleStatus
    next_run_at: str | None
    last_run_at: str | None
    run_count: int
    max_runs: int | None
    metadata: dict
    created_by: UUID
    created_at: str
    updated_at: str


def _to_response(schedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        organization_id=schedule.organization_id,
        content_id=schedule.content_id,
        name=schedule.name,
        platform=schedule.platform,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
        status=schedule.status,
        next_run_at=schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        run_count=schedule.run_count,
        max_runs=schedule.max_runs,
        metadata=schedule.metadata,
        created_by=schedule.created_by,
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


async def get_schedule_service(db: AsyncSession = Depends(get_db)) -> ContentScheduleService:
    return ContentScheduleService(
        ContentScheduleRepository(db),
        ContentRepositoryImpl(db),
        ContentPublishRepository(db),
    )


@router.post(
    "/content/schedules",
    status_code=status.HTTP_201_CREATED,
    summary="Create a recurring content schedule",
)
async def create_schedule(
    request: ScheduleCreateRequest,
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    schedule = await service.create_schedule(
        organization_id=request.organization_id,
        content_id=request.content_id,
        name=request.name,
        platform=request.platform,
        cron_expression=request.cron_expression,
        created_by=user_id,
        timezone=request.timezone,
        max_runs=request.max_runs,
        metadata=request.metadata,
    )
    return _to_response(schedule)


@router.get("/content/schedules", summary="List content schedules")
async def list_schedules(
    organization_id: UUID = Query(...),
    status: ScheduleStatus | None = Query(None),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleResponse]:
    await require_org_role(organization_id, "viewer", user_id, db)
    schedules = await service.list_schedules(organization_id, status)
    return [_to_response(s) for s in schedules]


@router.get("/content/schedules/{schedule_id}", summary="Get a content schedule")
async def get_schedule(
    schedule_id: UUID,
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return _to_response(schedule)


@router.patch("/content/schedules/{schedule_id}", summary="Update a content schedule")
async def update_schedule(
    schedule_id: UUID,
    request: ScheduleUpdateRequest,
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    await require_org_role(organization_id, "member", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    update_data = request.model_dump(exclude_unset=True)
    if "status" in update_data:
        status_val = update_data.pop("status")
        if status_val == ScheduleStatus.PAUSED:
            schedule = await service.pause_schedule(schedule_id)
        elif status_val == ScheduleStatus.ACTIVE:
            schedule = await service.resume_schedule(schedule_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid status transition",
            )

    if update_data:
        schedule = await service.update_schedule(schedule_id, **update_data)

    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return _to_response(schedule)


@router.post(
    "/content/schedules/{schedule_id}/pause",
    status_code=status.HTTP_200_OK,
    summary="Pause a content schedule",
)
async def pause_schedule(
    schedule_id: UUID,
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    await require_org_role(organization_id, "member", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    schedule = await service.pause_schedule(schedule_id)
    return _to_response(schedule)


@router.post(
    "/content/schedules/{schedule_id}/resume",
    status_code=status.HTTP_200_OK,
    summary="Resume a paused content schedule",
)
async def resume_schedule(
    schedule_id: UUID,
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    await require_org_role(organization_id, "member", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    schedule = await service.resume_schedule(schedule_id)
    return _to_response(schedule)


@router.delete(
    "/content/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a content schedule",
)
async def delete_schedule(
    schedule_id: UUID,
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    await service.delete_schedule(schedule_id)


@router.get(
    "/content/schedules/{schedule_id}/next-runs",
    summary="Preview next run times for a schedule",
)
async def preview_next_runs(
    schedule_id: UUID,
    count: int = Query(default=5, ge=1, le=20),
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    schedule = await service.get_schedule(schedule_id)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    from app.domain.services.workflow_scheduler import CronExpression

    cron = CronExpression.from_string(schedule.cron_expression)
    runs = []
    current = schedule.next_run_at or cron.next_trigger_time()
    for _ in range(count):
        runs.append(current.isoformat())
        current = cron.next_trigger_time(current)

    return {"schedule_id": str(schedule_id), "next_runs": runs}


@router.post(
    "/content/schedules/process-due",
    summary="Manually trigger processing of due schedules",
)
async def process_due_schedules(
    organization_id: UUID = Query(...),
    service: ContentScheduleService = Depends(get_schedule_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger processing of all due schedules for an organization."""
    await require_org_role(organization_id, "member", user_id, db)
    return await service.process_due_schedules()
