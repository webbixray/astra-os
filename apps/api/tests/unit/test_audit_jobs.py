from uuid import uuid4

from app.domain.entities.monitoring.audit_log import (
    AUDIT_ACTIONS,
    JOB_STATUSES,
    ApiUsageRecord,
    AuditLogEntry,
    JobRecord,
)


class TestAuditLogEntry:
    def test_defaults(self):
        entry = AuditLogEntry()
        assert entry.id is not None
        assert entry.organization_id is not None
        assert entry.user_id is not None
        assert entry.created_at is not None


class TestJobRecord:
    def test_create_defaults(self):
        job = JobRecord(
            organization_id=uuid4(),
            job_type="test_job",
        )
        assert job.status == "queued"
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.payload == {}
        assert job.result is None
        assert job.error_message == ""

    def test_start_sets_running_and_timestamp(self):
        job = JobRecord(organization_id=uuid4(), job_type="t")
        job.start()
        assert job.status == "running"
        assert job.started_at is not None
        assert job.updated_at is not None

    def test_complete_sets_completed(self):
        job = JobRecord(organization_id=uuid4(), job_type="t")
        job.complete({"rows": 42})
        assert job.status == "completed"
        assert job.completed_at is not None
        assert job.result == {"rows": 42}

    def test_complete_none_result(self):
        job = JobRecord(organization_id=uuid4(), job_type="t")
        job.complete(None)
        assert job.result is None

    def test_fail_increments_retry_count(self):
        job = JobRecord(organization_id=uuid4(), job_type="t", max_retries=3)
        assert job.retry_count == 0
        job.fail("error 1")
        assert job.status == "failed"
        assert job.error_message == "error 1"
        assert job.retry_count == 1
        job.fail("error 2")
        assert job.retry_count == 2
        job.fail("error 3")
        assert job.retry_count == 3

    def test_can_retry_boundary(self):
        job = JobRecord(organization_id=uuid4(), job_type="t", max_retries=3)
        assert job.can_retry() is True
        job.retry_count = 2
        assert job.can_retry() is True
        job.retry_count = 3
        assert job.can_retry() is False
        job.retry_count = 4
        assert job.can_retry() is False

    def test_default_max_retries(self):
        job = JobRecord(organization_id=uuid4(), job_type="t")
        assert job.max_retries == 3


class TestApiUsageRecord:
    def test_defaults(self):
        rec = ApiUsageRecord()
        assert rec.status_code == 200
        assert rec.response_time_ms == 0.0


class TestConstants:
    def test_audit_actions_not_empty(self):
        assert len(AUDIT_ACTIONS) >= 13
        assert "create" in AUDIT_ACTIONS
        assert "read" in AUDIT_ACTIONS

    def test_job_statuses_not_empty(self):
        assert len(JOB_STATUSES) == 5
        assert "queued" in JOB_STATUSES
        assert "running" in JOB_STATUSES
        assert "completed" in JOB_STATUSES
        assert "failed" in JOB_STATUSES
        assert "cancelled" in JOB_STATUSES
