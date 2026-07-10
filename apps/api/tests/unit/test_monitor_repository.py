from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.entities.monitoring.audit_log import ApiUsageRecord, AuditLogEntry, JobRecord
from app.infrastructure.db.repositories.monitoring.monitor_repository import (
    ApiUsageRepository,
    AuditLogRepository,
    JobRecordRepository,
)


@pytest.fixture
def session():
    s = MagicMock()
    s.flush = AsyncMock()
    s.execute = AsyncMock()
    return s


class TestAuditLogRepository:
    async def test_save(self, session):
        model_mock = MagicMock()
        model_mock.to_domain.return_value = AuditLogEntry(
            organization_id=uuid4(), user_id=uuid4(),
            action="view", resource_type="campaign",
        )
        with patch("app.infrastructure.db.repositories.monitoring.monitor_repository.AuditLogEntryModel") as MockModel:
            MockModel.from_domain.return_value = model_mock

            repo = AuditLogRepository(session)
            entry = AuditLogEntry(organization_id=uuid4(), user_id=uuid4(), action="view", resource_type="campaign")
            result = await repo.save(entry)

            assert result is not None
            session.add.assert_called_once_with(model_mock)
            session.flush.assert_awaited_once()

    async def test_find_by_org(self, session):
        m1 = MagicMock()
        m1.to_domain.return_value = AuditLogEntry(organization_id=uuid4(), user_id=uuid4(), action="view", resource_type="campaign")
        m2 = MagicMock()
        m2.to_domain.return_value = AuditLogEntry(organization_id=uuid4(), user_id=uuid4(), action="create", resource_type="campaign")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m1, m2]
        session.execute = AsyncMock(return_value=result_mock)

        repo = AuditLogRepository(session)
        results = await repo.find_by_org(uuid4(), limit=10)

        assert len(results) == 2

    async def test_find_by_org_with_filters(self, session):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = AuditLogRepository(session)
        results = await repo.find_by_org(uuid4(), action="view", resource_type="campaign", user_id=uuid4())

        assert results == []

    async def test_count_by_org(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 5
        session.execute = AsyncMock(return_value=result_mock)

        repo = AuditLogRepository(session)
        count = await repo.count_by_org(uuid4())

        assert count == 5

    async def test_count_by_org_with_filters(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 2
        session.execute = AsyncMock(return_value=result_mock)

        repo = AuditLogRepository(session)
        count = await repo.count_by_org(uuid4(), action="view")

        assert count == 2

    async def test_count_by_action(self, session):
        result_mock = MagicMock()
        result_mock.all.return_value = [("view", 3), ("create", 1)]
        session.execute = AsyncMock(return_value=result_mock)

        repo = AuditLogRepository(session)
        counts = await repo.count_by_action(uuid4())

        assert counts == {"view": 3, "create": 1}


class TestJobRecordRepository:
    async def test_save(self, session):
        model_mock = MagicMock()
        model_mock.to_domain.return_value = JobRecord(organization_id=uuid4(), job_type="email")
        with patch("app.infrastructure.db.repositories.monitoring.monitor_repository.JobRecordModel") as MockModel:
            MockModel.from_domain.return_value = model_mock

            repo = JobRecordRepository(session)
            job = JobRecord(organization_id=uuid4(), job_type="email")
            result = await repo.save(job)

            assert result is not None

    async def test_find_by_org(self, session):
        m = MagicMock()
        m.to_domain.return_value = JobRecord(organization_id=uuid4(), job_type="email")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m]
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        results = await repo.find_by_org(uuid4())

        assert len(results) == 1

    async def test_find_by_org_filtered(self, session):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        results = await repo.find_by_org(uuid4(), status="running", job_type="email")

        assert results == []

    async def test_find_by_id_found(self, session):
        m = MagicMock()
        m.to_domain.return_value = JobRecord(organization_id=uuid4(), job_type="email")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = m
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        result = await repo.find_by_id(uuid4())

        assert result is not None

    async def test_find_by_id_not_found(self, session):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        result = await repo.find_by_id(uuid4())

        assert result is None

    async def test_update_status(self, session):
        session.execute = AsyncMock()

        repo = JobRecordRepository(session)
        await repo.update_status(uuid4(), "completed", result={"key": "value"})

        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()

    async def test_count_by_org(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 10
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        count = await repo.count_by_org(uuid4())

        assert count == 10

    async def test_count_by_org_filtered(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 3
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        count = await repo.count_by_org(uuid4(), status="running")

        assert count == 3

    async def test_count_by_status(self, session):
        result_mock = MagicMock()
        result_mock.all.return_value = [("queued", 5), ("running", 2)]
        session.execute = AsyncMock(return_value=result_mock)

        repo = JobRecordRepository(session)
        counts = await repo.count_by_status(uuid4())

        assert counts == {"queued": 5, "running": 2}


class TestApiUsageRepository:
    async def test_save(self, session):
        model_mock = MagicMock()
        model_mock.to_domain.return_value = ApiUsageRecord(
            organization_id=uuid4(), user_id=uuid4(),
            endpoint="/health", method="GET", status_code=200,
        )
        with patch("app.infrastructure.db.repositories.monitoring.monitor_repository.ApiUsageRecordModel") as MockModel:
            MockModel.from_domain.return_value = model_mock

            repo = ApiUsageRepository(session)
            record = ApiUsageRecord(organization_id=uuid4(), user_id=uuid4(), endpoint="/health", method="GET", status_code=200)
            result = await repo.save(record)

            assert result is not None

    async def test_find_by_org(self, session):
        m = MagicMock()
        m.to_domain.return_value = ApiUsageRecord(organization_id=uuid4(), user_id=uuid4(), endpoint="/health", method="GET", status_code=200)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m]
        session.execute = AsyncMock(return_value=result_mock)

        repo = ApiUsageRepository(session)
        results = await repo.find_by_org(uuid4())

        assert len(results) == 1

    async def test_count_by_org(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 25
        session.execute = AsyncMock(return_value=result_mock)

        repo = ApiUsageRepository(session)
        count = await repo.count_by_org(uuid4())

        assert count == 25

    async def test_get_stats(self, session):
        result_mock = MagicMock()
        result_mock.one.return_value = (100, 45.5, 300.0)
        session.execute = AsyncMock(return_value=result_mock)

        repo = ApiUsageRepository(session)
        stats = await repo.get_stats(uuid4())

        assert stats["total_calls"] == 100
        assert stats["avg_response_time_ms"] == 45.5
        assert stats["max_response_time_ms"] == 300.0

    async def test_get_stats_zero(self, session):
        result_mock = MagicMock()
        result_mock.one.return_value = (0, None, None)
        session.execute = AsyncMock(return_value=result_mock)

        repo = ApiUsageRepository(session)
        stats = await repo.get_stats(uuid4())

        assert stats["total_calls"] == 0
        assert stats["avg_response_time_ms"] == 0
        assert stats["max_response_time_ms"] == 0

    async def test_count_by_endpoint(self, session):
        result_mock = MagicMock()
        result_mock.all.return_value = [("/health", "GET", 50, 12.3), ("/api/data", "POST", 30, 25.0)]
        session.execute = AsyncMock(return_value=result_mock)

        repo = ApiUsageRepository(session)
        endpoints = await repo.count_by_endpoint(uuid4())

        assert len(endpoints) == 2
        assert endpoints[0]["endpoint"] == "/health"
        assert endpoints[0]["avg_response_time_ms"] == 12.3
