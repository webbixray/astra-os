from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.common import now
from app.domain.entities.monitoring.audit_log import ApiUsageRecord, AuditLogEntry, JobRecord
from app.infrastructure.db.models.monitoring.audit_log_model import (
    ApiUsageRecordModel,
    AuditLogEntryModel,
    JobRecordModel,
)


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entry: AuditLogEntry) -> AuditLogEntry:
        model = AuditLogEntryModel.from_domain(entry)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_org(
        self,
        org_id: UUID,
        action: str | None = None,
        resource_type: str | None = None,
        user_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        query = select(AuditLogEntryModel).where(AuditLogEntryModel.organization_id == org_id)
        if action:
            query = query.where(AuditLogEntryModel.action == action)
        if resource_type:
            query = query.where(AuditLogEntryModel.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLogEntryModel.user_id == user_id)
        query = query.order_by(AuditLogEntryModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def count_by_org(
        self,
        org_id: UUID,
        action: str | None = None,
        resource_type: str | None = None,
        user_id: UUID | None = None,
    ) -> int:
        query = select(func.count()).where(AuditLogEntryModel.organization_id == org_id)
        if action:
            query = query.where(AuditLogEntryModel.action == action)
        if resource_type:
            query = query.where(AuditLogEntryModel.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLogEntryModel.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_action(self, org_id: UUID, since: datetime | None = None) -> dict[str, int]:
        query = select(AuditLogEntryModel.action, func.count()).where(
            AuditLogEntryModel.organization_id == org_id
        )
        if since:
            query = query.where(AuditLogEntryModel.created_at >= since)
        query = query.group_by(AuditLogEntryModel.action)
        result = await self.session.execute(query)
        return dict(result.all())


class JobRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, job: JobRecord) -> JobRecord:
        model = JobRecordModel.from_domain(job)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_org(
        self,
        org_id: UUID,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobRecord]:
        query = select(JobRecordModel).where(JobRecordModel.organization_id == org_id)
        if status:
            query = query.where(JobRecordModel.status == status)
        if job_type:
            query = query.where(JobRecordModel.job_type == job_type)
        query = query.order_by(JobRecordModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_id(self, job_id: UUID) -> JobRecord | None:
        result = await self.session.execute(
            select(JobRecordModel).where(JobRecordModel.id == job_id)
        )
        m = result.scalar_one_or_none()
        return m.to_domain() if m else None

    async def update_status(self, job_id: UUID, status: str, **kwargs) -> None:
        values = {"status": status, "updated_at": now()}
        values.update(kwargs)
        await self.session.execute(
            update(JobRecordModel).where(JobRecordModel.id == job_id).values(**values)
        )
        await self.session.flush()

    async def count_by_org(
        self,
        org_id: UUID,
        status: str | None = None,
        job_type: str | None = None,
    ) -> int:
        query = select(func.count()).where(JobRecordModel.organization_id == org_id)
        if status:
            query = query.where(JobRecordModel.status == status)
        if job_type:
            query = query.where(JobRecordModel.job_type == job_type)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_status(self, org_id: UUID) -> dict[str, int]:
        query = (
            select(JobRecordModel.status, func.count())
            .where(JobRecordModel.organization_id == org_id)
            .group_by(JobRecordModel.status)
        )
        result = await self.session.execute(query)
        return dict(result.all())


class ApiUsageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, record: ApiUsageRecord) -> ApiUsageRecord:
        model = ApiUsageRecordModel.from_domain(record)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_org(
        self,
        org_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ApiUsageRecord]:
        result = await self.session.execute(
            select(ApiUsageRecordModel)
            .where(ApiUsageRecordModel.organization_id == org_id)
            .order_by(ApiUsageRecordModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def count_by_org(self, org_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).where(ApiUsageRecordModel.organization_id == org_id)
        )
        return result.scalar() or 0

    async def get_stats(
        self,
        org_id: UUID,
        since: datetime | None = None,
    ) -> dict:
        query = select(
            func.count(),
            func.avg(ApiUsageRecordModel.response_time_ms),
            func.max(ApiUsageRecordModel.response_time_ms),
        ).where(ApiUsageRecordModel.organization_id == org_id)
        if since:
            query = query.where(ApiUsageRecordModel.created_at >= since)
        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_calls": row[0] or 0,
            "avg_response_time_ms": round(row[1] or 0, 2),
            "max_response_time_ms": row[2] or 0,
        }

    async def count_by_endpoint(self, org_id: UUID, since: datetime | None = None) -> list[dict]:
        query = select(
            ApiUsageRecordModel.endpoint,
            ApiUsageRecordModel.method,
            func.count(),
            func.avg(ApiUsageRecordModel.response_time_ms),
        ).where(ApiUsageRecordModel.organization_id == org_id)
        if since:
            query = query.where(ApiUsageRecordModel.created_at >= since)
        query = query.group_by(ApiUsageRecordModel.endpoint, ApiUsageRecordModel.method)
        result = await self.session.execute(query)
        return [
            {
                "endpoint": r[0],
                "method": r[1],
                "count": r[2],
                "avg_response_time_ms": round(r[3] or 0, 2),
            }
            for r in result.all()
        ]
