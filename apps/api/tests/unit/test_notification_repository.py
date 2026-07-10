from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.entities.notifications.notification import Notification
from app.infrastructure.db.repositories.notification_repository import NotificationRepository


@pytest.fixture
def session():
    s = MagicMock()
    s.flush = AsyncMock()
    s.execute = AsyncMock()
    return s


class TestSave:
    async def test_save(self, session):
        model = MagicMock()
        model.to_domain.return_value = Notification(user_id=uuid4(), organization_id=uuid4(), type="info", title="Test")
        with patch("app.infrastructure.db.repositories.notification_repository.NotificationModel") as MockModel:
            MockModel.from_domain.return_value = model

            repo = NotificationRepository(session)
            n = Notification(user_id=uuid4(), organization_id=uuid4(), type="info", title="Test")
            result = await repo.save(n)

            assert result is not None
            session.add.assert_called_once_with(model)
            session.flush.assert_awaited_once()


class TestFindByUser:
    async def test_find_by_user(self, session):
        m = MagicMock()
        m.to_domain.return_value = Notification(user_id=uuid4(), organization_id=uuid4(), type="info", title="Test")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m]
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        results = await repo.find_by_user(uuid4(), uuid4())

        assert len(results) == 1

    async def test_with_filters(self, session):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        results = await repo.find_by_user(uuid4(), uuid4(), unread_only=True, channel="email")

        assert results == []

    async def test_no_archive(self, session):
        m = MagicMock()
        m.to_domain.return_value = Notification(user_id=uuid4(), organization_id=uuid4(), type="info", title="Test")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m]
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        results = await repo.find_by_user(uuid4(), uuid4(), archived=True)

        assert len(results) == 1


class TestCountByUser:
    async def test_count(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 5
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.count_by_user(uuid4(), uuid4())

        assert count == 5

    async def test_count_with_filters(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 2
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.count_by_user(uuid4(), uuid4(), unread_only=True, channel="in_app")

        assert count == 2

    async def test_count_zero(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 0
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.count_by_user(uuid4(), uuid4())

        assert count == 0


class TestCountUnread:
    async def test_count_unread(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 3
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.count_unread(uuid4(), uuid4())

        assert count == 3

    async def test_count_unread_with_channel(self, session):
        result_mock = MagicMock()
        result_mock.scalar.return_value = 1
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.count_unread(uuid4(), uuid4(), channel="email")

        assert count == 1


class TestMarkRead:
    async def test_mark_read(self, session):
        session.execute = AsyncMock()

        repo = NotificationRepository(session)
        await repo.mark_read(uuid4())

        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()

    async def test_mark_all_read(self, session):
        result_mock = MagicMock()
        result_mock.rowcount = 3
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        count = await repo.mark_all_read(uuid4(), uuid4())

        assert count == 3


class TestArchive:
    async def test_archive(self, session):
        session.execute = AsyncMock()

        repo = NotificationRepository(session)
        await repo.archive(uuid4())

        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()


class TestSearch:
    async def test_search(self, session):
        m = MagicMock()
        m.to_domain.return_value = Notification(user_id=uuid4(), organization_id=uuid4(), type="info", title="Test")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [m]
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        results = await repo.search(uuid4(), uuid4(), "test")

        assert len(results) == 1

    async def test_search_empty(self, session):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NotificationRepository(session)
        results = await repo.search(uuid4(), uuid4(), "nonexistent")

        assert results == []
