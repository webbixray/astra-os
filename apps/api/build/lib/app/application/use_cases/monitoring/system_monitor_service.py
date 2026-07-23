from datetime import timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.common import now
from app.domain.entities.monitoring.audit_log import (
    AUDIT_ACTIONS,
    JOB_STATUSES,
    ApiUsageRecord,
    AuditLogEntry,
    JobRecord,
)
from app.domain.exceptions.domain_exceptions import ValidationError
from app.infrastructure.db.repositories.monitoring.monitor_repository import (
    ApiUsageRepository,
    AuditLogRepository,
    JobRecordRepository,
)


class SystemMonitorService:
    def __init__(
        self,
        session: AsyncSession,
        audit_repo: AuditLogRepository,
        job_repo: JobRecordRepository,
        usage_repo: ApiUsageRepository,
    ):
        self.session = session
        self.audit_repo = audit_repo
        self.job_repo = job_repo
        self.usage_repo = usage_repo

    # ── Audit Log ────────────────────────────────────────────────────────────

    async def log_action(
        self,
        org_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str = "",
        details: dict | None = None,
        ip_address: str = "",
    ) -> AuditLogEntry:
        if action not in AUDIT_ACTIONS:
            raise ValidationError(f"Unknown audit action: {action}")
        entry = AuditLogEntry(
            organization_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        return await self.audit_repo.save(entry)

    async def get_audit_logs(
        self,
        org_id: UUID,
        action: str | None = None,
        resource_type: str | None = None,
        user_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        entries = await self.audit_repo.find_by_org(
            org_id,
            action,
            resource_type,
            user_id,
            limit,
            offset,
        )
        total = await self.audit_repo.count_by_org(org_id, action, resource_type, user_id)
        items = [
            {
                "id": str(e.id),
                "user_id": str(e.user_id),
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "details": e.details,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
        return {"items": items, "total": total}

    async def get_audit_summary(self, org_id: UUID, hours: int = 24) -> dict:
        since = now() - timedelta(hours=hours)
        counts = await self.audit_repo.count_by_action(org_id, since)
        return {"period_hours": hours, "actions": counts, "total": sum(counts.values())}

    # ── Job Records ──────────────────────────────────────────────────────────

    async def create_job(
        self,
        org_id: UUID,
        job_type: str,
        payload: dict | None = None,
        max_retries: int = 3,
    ) -> JobRecord:
        job = JobRecord(
            organization_id=org_id,
            job_type=job_type,
            payload=payload or {},
            max_retries=max_retries,
        )
        return await self.job_repo.save(job)

    async def get_jobs(
        self,
        org_id: UUID,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        jobs = await self.job_repo.find_by_org(org_id, status, job_type, limit, offset)
        total = await self.job_repo.count_by_org(org_id, status, job_type)
        items = [
            {
                "id": str(j.id),
                "job_type": j.job_type,
                "status": j.status,
                "payload": j.payload,
                "result": j.result,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "error_message": j.error_message,
                "retry_count": j.retry_count,
                "max_retries": j.max_retries,
                "created_at": j.created_at.isoformat(),
            }
            for j in jobs
        ]
        return {"items": items, "total": total}

    async def update_job_status(
        self,
        job_id: UUID,
        status: str,
        result: dict | None = None,
        error_message: str = "",
    ) -> JobRecord:
        if status not in JOB_STATUSES:
            raise ValidationError(f"Unknown job status: {status}")
        job = await self.job_repo.find_by_id(job_id)
        if not job:
            raise ValidationError("Job not found")
        kwargs = {}
        if status == "running":
            kwargs["started_at"] = now()
        elif status == "completed":
            kwargs["completed_at"] = now()
            kwargs["result"] = result
        elif status == "failed":
            kwargs["error_message"] = error_message
            kwargs["retry_count"] = job.retry_count + 1
        await self.job_repo.update_status(job_id, status, **kwargs)
        job.status = status
        return job

    async def retry_job(self, job_id: UUID) -> JobRecord:
        job = await self.job_repo.find_by_id(job_id)
        if not job:
            raise ValidationError("Job not found")
        if not job.can_retry():
            raise ValidationError("Max retries exceeded")
        await self.job_repo.update_status(
            job_id,
            "queued",
            error_message="",
            started_at=None,
            completed_at=None,
        )
        job.status = "queued"
        return job

    async def get_job_summary(self, org_id: UUID) -> dict:
        counts = await self.job_repo.count_by_status(org_id)
        total = sum(counts.values())
        return {"total": total, "by_status": counts}

    # ── API Usage ────────────────────────────────────────────────────────────

    async def record_api_call(
        self,
        org_id: UUID,
        user_id: UUID,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: str = "",
        response_time_ms: float = 0.0,
    ) -> ApiUsageRecord:
        record = ApiUsageRecord(
            organization_id=org_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            ip_address=ip_address,
            response_time_ms=response_time_ms,
        )
        return await self.usage_repo.save(record)

    async def get_usage_records(
        self,
        org_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        records = await self.usage_repo.find_by_org(org_id, limit, offset)
        total = await self.usage_repo.count_by_org(org_id)
        items = [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "endpoint": r.endpoint,
                "method": r.method,
                "status_code": r.status_code,
                "ip_address": r.ip_address,
                "response_time_ms": r.response_time_ms,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]
        return {"items": items, "total": total}

    async def get_usage_stats(
        self,
        org_id: UUID,
        hours: int = 24,
    ) -> dict:
        since = now() - timedelta(hours=hours)
        stats = await self.usage_repo.get_stats(org_id, since)
        by_endpoint = await self.usage_repo.count_by_endpoint(org_id, since)
        return {
            "period_hours": hours,
            "total_calls": stats["total_calls"],
            "avg_response_time_ms": stats["avg_response_time_ms"],
            "max_response_time_ms": stats["max_response_time_ms"],
            "by_endpoint": by_endpoint,
        }

    # ── System Health ────────────────────────────────────────────────────────

    async def check_health(self) -> dict:
        checks = {}
        overall = "healthy"

        # Database check
        try:
            start = now()
            await self.session.execute(text("SELECT 1"))
            db_ms = (now() - start).total_seconds() * 1000
            checks["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_ms, 2),
            }
        except Exception as e:
            checks["database"] = {"status": "down", "error": str(e)}
            overall = "degraded"

        current_time = now().isoformat()
        return {
            "status": overall,
            "timestamp": current_time,
            "uptime": None,
            "checks": checks,
        }
