from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.content.content_publishing_service import (
    ContentPublishingService,
    _to_response,
)
from app.domain.entities.content.content_publish import ContentPublish
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def content_repo():
    return MagicMock()


@pytest.fixture
def service(repo, content_repo):
    return ContentPublishingService(repo=repo, content_repo=content_repo)


VALID_PLATFORM = "website"


def make_publish(**overrides: dict) -> MagicMock:
    p = MagicMock(spec=ContentPublish)
    p.id = overrides.get("id", uuid4())
    p.content_id = overrides.get("content_id", uuid4())
    p.platform = overrides.get("platform", VALID_PLATFORM)
    p.status = overrides.get("status", "draft")
    p.scheduled_at = overrides.get("scheduled_at")
    p.published_at = overrides.get("published_at")
    p.external_url = overrides.get("external_url")
    p.error_message = overrides.get("error_message")
    p.metadata = overrides.get("metadata", {})
    p.created_at = overrides.get("created_at", datetime.now(UTC))
    p.mark_publishing = MagicMock()
    p.mark_published = MagicMock()
    p.mark_failed = MagicMock()
    return p


class TestToResponse:
    def test_with_scheduled_at(self):
        p = make_publish(
            status="scheduled",
            scheduled_at=datetime(2025, 6, 1, 10, 0, tzinfo=UTC),
        )

        resp = _to_response(p)

        assert resp["id"] == str(p.id)
        assert resp["platform"] == VALID_PLATFORM
        assert resp["status"] == "scheduled"
        assert resp["scheduled_at"] == "2025-06-01T10:00:00+00:00"

    def test_without_scheduled_at(self):
        p = make_publish(status="draft")

        resp = _to_response(p)

        assert resp["scheduled_at"] is None
        assert resp["published_at"] is None
        assert resp["external_url"] is None
        assert resp["error_message"] is None


class TestPublish:
    async def test_publish_with_schedule(self, service):
        saved_pub = make_publish(status="scheduled")
        service.repo.save = AsyncMock(return_value=saved_pub)

        result = await service.publish(
            content_id=uuid4(),
            platform=VALID_PLATFORM,
            scheduled_at="2025-06-15T10:00:00+00:00",
        )

        assert result == saved_pub
        assert service.repo.save.call_count == 1

    async def test_publish_immediate_no_adapter(self, service):
        service.repo.save = AsyncMock(side_effect=lambda p: p)
        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=None,
        ):
            with pytest.raises(ValidationError, match="No adapter found for platform"):
                await service.publish(content_id=uuid4(), platform=VALID_PLATFORM)

    async def test_publish_immediate_success(self, service):
        saved_pub = make_publish(status="draft")
        service.repo.save = AsyncMock(return_value=saved_pub)

        adapter = MagicMock()
        adapter.publish = AsyncMock(return_value="https://example.com/post/1")

        content = MagicMock()
        content.id = uuid4()
        service._content_repo.find_by_id = AsyncMock(return_value=content)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            result = await service.publish(content_id=uuid4(), platform=VALID_PLATFORM)

        assert result == saved_pub
        saved_pub.mark_publishing.assert_called_once()
        adapter.publish.assert_awaited_once()
        saved_pub.mark_published.assert_called_once_with("https://example.com/post/1")
        assert service.repo.save.call_count == 3

    async def test_publish_immediate_adapter_error(self, service):
        saved_pub = make_publish(status="draft")
        service.repo.save = AsyncMock(return_value=saved_pub)

        adapter = MagicMock()
        adapter.publish = AsyncMock(side_effect=ValueError("API timeout"))

        content = MagicMock()
        content.id = uuid4()
        service._content_repo.find_by_id = AsyncMock(return_value=content)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            await service.publish(content_id=uuid4(), platform=VALID_PLATFORM)

        saved_pub.mark_failed.assert_called_once_with("API timeout")
        assert service.repo.save.call_count == 3

    async def test_publish_content_not_found(self, service):
        saved_pub = make_publish(status="draft")
        service.repo.save = AsyncMock(return_value=saved_pub)

        adapter = MagicMock()
        adapter.publish = AsyncMock()

        service._content_repo.find_by_id = AsyncMock(return_value=None)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            with pytest.raises(EntityNotFoundError):
                await service.publish(content_id=uuid4(), platform=VALID_PLATFORM)

    async def test_publish_no_content_repo(self, service):
        service_no_repo = ContentPublishingService(repo=service.repo, content_repo=None)
        service_no_repo.repo.save = AsyncMock(return_value=make_publish(status="draft"))

        adapter = MagicMock()
        adapter.publish = AsyncMock()

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            with pytest.raises(ValidationError, match="Content repository not available"):
                await service_no_repo.publish(content_id=uuid4(), platform=VALID_PLATFORM)


class TestSchedule:
    async def test_schedule(self, service):
        expected = make_publish(status="scheduled")
        service.repo.save = AsyncMock(return_value=expected)

        result = await service.schedule(
            content_id=uuid4(),
            platform=VALID_PLATFORM,
            scheduled_at="2025-06-15T10:00:00+00:00",
        )

        assert result == expected


class TestGetQueue:
    async def test_get_queue_all(self, service):
        p1 = make_publish(status="scheduled")
        p2 = make_publish(status="draft")
        service.repo.find_queue_by_org = AsyncMock(return_value=[p1, p2])

        result = await service.get_queue(uuid4())

        assert len(result) == 2
        assert result[0]["status"] == "scheduled"

    async def test_get_queue_filtered(self, service):
        p = make_publish(status="scheduled")
        service.repo.find_queue_by_org = AsyncMock(return_value=[p])

        result = await service.get_queue(uuid4(), status="scheduled")

        assert len(result) == 1
        assert result[0]["status"] == "scheduled"

    async def test_get_queue_empty(self, service):
        service.repo.find_queue_by_org = AsyncMock(return_value=[])

        result = await service.get_queue(uuid4())

        assert result == []


class TestGetHistory:
    async def test_get_history(self, service):
        p = make_publish(status="published")
        service.repo.find_by_content = AsyncMock(return_value=[p])

        result = await service.get_history(uuid4())

        assert len(result) == 1
        assert result[0]["status"] == "published"


class TestCancel:
    async def test_cancel_scheduled(self, service):
        p = make_publish(status="scheduled")
        service.repo.find_by_id = AsyncMock(return_value=p)
        service.repo.delete = AsyncMock()

        await service.cancel(uuid4())

        service.repo.delete.assert_awaited_once()

    async def test_cancel_publishing(self, service):
        p = make_publish(status="publishing")
        service.repo.find_by_id = AsyncMock(return_value=p)
        service.repo.delete = AsyncMock()

        await service.cancel(uuid4())

        service.repo.delete.assert_awaited_once()

    async def test_cancel_not_found(self, service):
        service.repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.cancel(uuid4())

    async def test_cancel_invalid_status(self, service):
        p = make_publish(status="published")
        service.repo.find_by_id = AsyncMock(return_value=p)

        with pytest.raises(ValidationError, match="Cannot cancel"):
            await service.cancel(uuid4())


class TestRetry:
    async def test_retry_success(self, service):
        p = make_publish(status="failed", platform=VALID_PLATFORM)
        service.repo.find_by_id = AsyncMock(return_value=p)
        service.repo.save = AsyncMock(return_value=p)

        adapter = MagicMock()
        adapter.publish = AsyncMock(return_value="https://example.com/retry")

        content = MagicMock()
        content.id = uuid4()
        service._content_repo.find_by_id = AsyncMock(return_value=content)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            result = await service.retry(uuid4())

        assert result == p
        p.mark_publishing.assert_called_once()
        p.mark_published.assert_called_once_with("https://example.com/retry")

    async def test_retry_adapter_error(self, service):
        p = make_publish(status="failed", platform=VALID_PLATFORM)
        service.repo.find_by_id = AsyncMock(return_value=p)
        service.repo.save = AsyncMock(return_value=p)

        adapter = MagicMock()
        adapter.publish = AsyncMock(side_effect=RuntimeError("Network error"))

        content = MagicMock()
        content.id = uuid4()
        service._content_repo.find_by_id = AsyncMock(return_value=content)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=adapter,
        ):
            await service.retry(uuid4())

        p.mark_failed.assert_called_once_with("Network error")

    async def test_retry_not_found(self, service):
        service.repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.retry(uuid4())

    async def test_retry_not_failed(self, service):
        p = make_publish(status="published")
        service.repo.find_by_id = AsyncMock(return_value=p)

        with pytest.raises(ValidationError, match="only retry failed"):
            await service.retry(uuid4())

    async def test_retry_no_adapter(self, service):
        p = make_publish(status="failed", platform="unknown")
        service.repo.find_by_id = AsyncMock(return_value=p)

        with patch(
            "app.application.use_cases.content.content_publishing_service.get_adapter",
            return_value=None,
        ):
            with pytest.raises(ValidationError, match="No adapter found"):
                await service.retry(uuid4())
