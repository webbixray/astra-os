from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.monitoring.system_monitor_service import SystemMonitorService
from app.domain.entities.monitoring.audit_log import (
    ApiUsageRecord,
    AuditLogEntry,
    JobRecord,
)
from app.domain.exceptions.domain_exceptions import ValidationError


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def audit_repo():
    return MagicMock()


@pytest.fixture
def job_repo():
    return MagicMock()


@pytest.fixture
def usage_repo():
    return MagicMock()


@pytest.fixture
def service(session, audit_repo, job_repo, usage_repo):
    return SystemMonitorService(
        session=session,
        audit_repo=audit_repo,
        job_repo=job_repo,
        usage_repo=usage_repo,
    )


class TestLogAction:
    async def test_log_action_success(self, service, audit_repo):
        audit_repo.save = AsyncMock(return_value=AuditLogEntry(
            organization_id=uuid4(), user_id=uuid4(),
            action="read", resource_type="campaign",
        ))

        result = await service.log_action(uuid4(), uuid4(), "read", "campaign")

        assert result.action == "read"

    async def test_log_action_invalid_action(self, service):
        with pytest.raises(ValidationError, match="Unknown audit action"):
            await service.log_action(uuid4(), uuid4(), "invalid_action", "campaign")


class TestGetAuditLogs:
    async def test_get_audit_logs(self, service, audit_repo):
        entry = AuditLogEntry(
            organization_id=uuid4(), user_id=uuid4(),
            action="view", resource_type="campaign",
        )
        audit_repo.find_by_org = AsyncMock(return_value=[entry])
        audit_repo.count_by_org = AsyncMock(return_value=1)

        result = await service.get_audit_logs(uuid4())

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["action"] == "view"


class TestGetAuditSummary:
    async def test_get_audit_summary(self, service, audit_repo):
        audit_repo.count_by_action = AsyncMock(return_value={"view": 5, "create": 2})

        result = await service.get_audit_summary(uuid4(), hours=48)

        assert result["period_hours"] == 48
        assert result["total"] == 7
        assert result["actions"]["view"] == 5


class TestCreateJob:
    async def test_create_job(self, service, job_repo):
        job_repo.save = AsyncMock(return_value=JobRecord(
            organization_id=uuid4(), job_type="email",
        ))

        result = await service.create_job(uuid4(), "email")

        assert result.job_type == "email"


class TestGetJobs:
    async def test_get_jobs(self, service, job_repo):
        job = JobRecord(organization_id=uuid4(), job_type="email")
        job_repo.find_by_org = AsyncMock(return_value=[job])
        job_repo.count_by_org = AsyncMock(return_value=1)

        result = await service.get_jobs(uuid4())

        assert result["total"] == 1
        assert len(result["items"]) == 1

    async def test_get_jobs_filtered(self, service, job_repo):
        job_repo.find_by_org = AsyncMock(return_value=[])
        job_repo.count_by_org = AsyncMock(return_value=0)

        result = await service.get_jobs(uuid4(), status="running", job_type="email")

        assert result["total"] == 0


class TestUpdateJobStatus:
    async def test_update_to_running(self, service, job_repo):
        job = MagicMock(spec=JobRecord)
        job.retry_count = 0
        job_repo.find_by_id = AsyncMock(return_value=job)
        job_repo.update_status = AsyncMock()

        result = await service.update_job_status(uuid4(), "running")

        assert result.status == "running"

    async def test_update_to_completed(self, service, job_repo):
        job = MagicMock(spec=JobRecord)
        job_repo.find_by_id = AsyncMock(return_value=job)
        job_repo.update_status = AsyncMock()

        result = await service.update_job_status(uuid4(), "completed", result={"ok": True})

        assert result.status == "completed"

    async def test_update_to_failed(self, service, job_repo):
        job = MagicMock(spec=JobRecord)
        job.retry_count = 0
        job_repo.find_by_id = AsyncMock(return_value=job)
        job_repo.update_status = AsyncMock()

        result = await service.update_job_status(uuid4(), "failed", error_message="Timeout")

        assert result.status == "failed"

    async def test_invalid_status(self, service):
        with pytest.raises(ValidationError, match="Unknown job status"):
            await service.update_job_status(uuid4(), "nonexistent")

    async def test_job_not_found(self, service, job_repo):
        job_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValidationError, match="Job not found"):
            await service.update_job_status(uuid4(), "completed")


class TestRetryJob:
    async def test_retry_job_success(self, service, job_repo):
        job = MagicMock(spec=JobRecord)
        job.can_retry.return_value = True
        job_repo.find_by_id = AsyncMock(return_value=job)
        job_repo.update_status = AsyncMock()

        result = await service.retry_job(uuid4())

        assert result.status == "queued"

    async def test_retry_job_not_found(self, service, job_repo):
        job_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValidationError, match="Job not found"):
            await service.retry_job(uuid4())

    async def test_retry_job_max_retries(self, service, job_repo):
        job = MagicMock(spec=JobRecord)
        job.can_retry.return_value = False
        job_repo.find_by_id = AsyncMock(return_value=job)

        with pytest.raises(ValidationError, match="Max retries exceeded"):
            await service.retry_job(uuid4())


class TestGetJobSummary:
    async def test_get_job_summary(self, service, job_repo):
        job_repo.count_by_status = AsyncMock(return_value={"queued": 5, "running": 2})

        result = await service.get_job_summary(uuid4())

        assert result["total"] == 7
        assert result["by_status"]["queued"] == 5


class TestRecordApiCall:
    async def test_record_api_call(self, service, usage_repo):
        usage_repo.save = AsyncMock(return_value=ApiUsageRecord(
            organization_id=uuid4(), user_id=uuid4(),
            endpoint="/health", method="GET", status_code=200,
        ))

        result = await service.record_api_call(uuid4(), uuid4(), "/health", "GET", 200)

        assert result.endpoint == "/health"


class TestGetUsageRecords:
    async def test_get_usage_records(self, service, usage_repo):
        record = ApiUsageRecord(organization_id=uuid4(), user_id=uuid4(), endpoint="/health", method="GET", status_code=200)
        usage_repo.find_by_org = AsyncMock(return_value=[record])
        usage_repo.count_by_org = AsyncMock(return_value=1)

        result = await service.get_usage_records(uuid4())

        assert result["total"] == 1
        assert len(result["items"]) == 1


class TestGetUsageStats:
    async def test_get_usage_stats(self, service, usage_repo):
        usage_repo.get_stats = AsyncMock(return_value={"total_calls": 100, "avg_response_time_ms": 45.5, "max_response_time_ms": 300.0})
        usage_repo.count_by_endpoint = AsyncMock(return_value=[{"endpoint": "/health", "method": "GET", "count": 50, "avg_response_time_ms": 12.3}])

        result = await service.get_usage_stats(uuid4(), hours=48)

        assert result["period_hours"] == 48
        assert result["total_calls"] == 100
        assert len(result["by_endpoint"]) == 1


class TestCheckHealth:
    async def test_healthy(self, service, session):
        session.execute = AsyncMock()

        result = await service.check_health()

        assert result["status"] == "healthy"
        assert "database" in result["checks"]
        assert result["checks"]["database"]["status"] == "healthy"

    async def test_database_down(self, service, session):
        session.execute = AsyncMock(side_effect=Exception("Connection refused"))

        result = await service.check_health()

        assert result["status"] == "degraded"
        assert result["checks"]["database"]["status"] == "down"
