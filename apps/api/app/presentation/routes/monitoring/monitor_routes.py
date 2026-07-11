from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.monitoring.system_monitor_service import SystemMonitorService
from app.domain.exceptions.domain_exceptions import ValidationError
from app.infrastructure.db.repositories.monitoring.monitor_repository import (
    ApiUsageRepository,
    AuditLogRepository,
    JobRecordRepository,
)
from app.presentation.dependencies import get_db, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import PaginatedResponse

router = APIRouter()


class LogActionRequest(BaseModel):
    action: str
    resource_type: str
    resource_id: str = ""
    details: dict = {}
    ip_address: str = ""


class CreateJobRequest(BaseModel):
    job_type: str
    payload: dict = {}
    max_retries: int = 3


class UpdateJobStatusRequest(BaseModel):
    status: str
    result: dict | None = None
    error_message: str = ""


class RecordApiCallRequest(BaseModel):
    endpoint: str
    method: str
    status_code: int = 200
    ip_address: str = ""
    response_time_ms: float = 0.0


def get_service(db: AsyncSession = Depends(get_db)) -> SystemMonitorService:
    return SystemMonitorService(
        session=db,
        audit_repo=AuditLogRepository(db),
        job_repo=JobRecordRepository(db),
        usage_repo=ApiUsageRepository(db),
    )


# ── Audit Log ────────────────────────────────────────────────────────────────

@router.post("/audit-logs", status_code=status.HTTP_201_CREATED, summary="Log audit action")
async def log_action(
    request: LogActionRequest,
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        entry = await service.log_action(
            org_id=organization_id, user_id=user_id,
            action=request.action, resource_type=request.resource_type,
            resource_id=request.resource_id, details=request.details,
            ip_address=request.ip_address,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(entry.id), "action": entry.action, "created_at": entry.created_at.isoformat()}


@router.get("/audit-logs", summary="Get audit logs")
async def get_audit_logs(
    organization_id: UUID = Query(...),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    user_id: UUID | None = Query(None),
    service: SystemMonitorService = Depends(get_service),
    user_id_auth: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(pagination_params),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id_auth, db)
    page = pagination["page"]
    limit = pagination["limit"]
    offset = (page - 1) * limit
    result = await service.get_audit_logs(
        org_id=organization_id, action=action,
        resource_type=resource_type, user_id=user_id,
        limit=limit, offset=offset,
    )
    return PaginatedResponse(
        data=result["items"],
        total=result["total"],
        page=page,
        limit=limit,
        pages=max(1, (result["total"] + limit - 1) // limit),
    )


@router.get("/audit-logs/summary", summary="Get audit log summary")
async def get_audit_summary(
    organization_id: UUID = Query(...),
    hours: int = Query(24),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_audit_summary(org_id=organization_id, hours=hours)


# ── Jobs ─────────────────────────────────────────────────────────────────────

@router.post("/jobs", status_code=status.HTTP_201_CREATED, summary="Create background job")
async def create_job(
    request: CreateJobRequest,
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    job = await service.create_job(
        org_id=organization_id, job_type=request.job_type,
        payload=request.payload, max_retries=request.max_retries,
    )
    return {"id": str(job.id), "job_type": job.job_type, "status": job.status}


@router.get("/jobs", summary="List background jobs")
async def get_jobs(
    organization_id: UUID = Query(...),
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(pagination_params),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    page = pagination["page"]
    limit = pagination["limit"]
    offset = (page - 1) * limit
    result = await service.get_jobs(
        org_id=organization_id, status=status,
        job_type=job_type, limit=limit, offset=offset,
    )
    return PaginatedResponse(
        data=result["items"],
        total=result["total"],
        page=page,
        limit=limit,
        pages=max(1, (result["total"] + limit - 1) // limit),
    )


@router.patch("/jobs/{job_id}/status", summary="Update job status")
async def update_job_status(
    job_id: UUID,
    request: UpdateJobStatusRequest,
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    existing_job = await service.job_repo.find_by_id(job_id)
    if not existing_job or existing_job.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from None
    try:
        job = await service.update_job_status(
            job_id=job_id, status=request.status,
            result=request.result, error_message=request.error_message,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(job.id), "status": job.status}


@router.post("/jobs/{job_id}/retry", summary="Retry failed job")
async def retry_job(
    job_id: UUID,
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "admin", user_id, db)
    existing_job = await service.job_repo.find_by_id(job_id)
    if not existing_job or existing_job.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from None
    try:
        job = await service.retry_job(job_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(job.id), "status": job.status}


@router.get("/jobs/summary", summary="Get job summary")
async def get_job_summary(
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_job_summary(org_id=organization_id)


# ── API Usage ────────────────────────────────────────────────────────────────

@router.post("/usage-records", status_code=status.HTTP_201_CREATED, summary="Record API usage")
async def record_api_call(
    request: RecordApiCallRequest,
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    record = await service.record_api_call(
        org_id=organization_id, user_id=user_id,
        endpoint=request.endpoint, method=request.method,
        status_code=request.status_code, ip_address=request.ip_address,
        response_time_ms=request.response_time_ms,
    )
    return {"id": str(record.id), "endpoint": record.endpoint, "method": record.method}


@router.get("/usage-records", summary="Get API usage records")
async def get_usage_records(
    organization_id: UUID = Query(...),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(pagination_params),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    page = pagination["page"]
    limit = pagination["limit"]
    offset = (page - 1) * limit
    result = await service.get_usage_records(org_id=organization_id, limit=limit, offset=offset)
    return PaginatedResponse(
        data=result["items"],
        total=result["total"],
        page=page,
        limit=limit,
        pages=max(1, (result["total"] + limit - 1) // limit),
    )


@router.get("/usage-records/stats", summary="Get API usage stats")
async def get_usage_stats(
    organization_id: UUID = Query(...),
    hours: int = Query(24),
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.get_usage_stats(org_id=organization_id, hours=hours)


# ── System Health ────────────────────────────────────────────────────────────

@router.get("/system/health", summary="Check system health")
async def check_system_health(
    service: SystemMonitorService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    return await service.check_health()
