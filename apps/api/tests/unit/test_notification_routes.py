import hashlib
import hmac
import secrets
import time
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import config
from app.main import create_app
from app.presentation.middleware.auth import require_user_id

_MOCK_USER_ID = uuid4()


def _mock_db_session() -> MagicMock:
    mock_member = MagicMock()
    mock_member.role = "owner"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


@pytest.fixture
def app() -> FastAPI:
    a = create_app()
    a.state.db = MagicMock(return_value=_mock_db_session())
    a.dependency_overrides[require_user_id] = lambda: _MOCK_USER_ID
    yield a
    a.dependency_overrides.clear()


@pytest.fixture
async def test_client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


def _setup_csrf(client: AsyncClient) -> dict[str, str]:
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
    return {"X-CSRF-Token": csrf_token}


class TestNotificationHubRoutes:
    endpoint_prefix = "/api/v1"

    @pytest.mark.asyncio
    async def test_list_notifications(self, app: FastAPI, test_client: AsyncClient):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.list_notifications = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "type": "campaign_milestone",
                        "title": "Campaign Launched",
                        "body": "Your campaign is live",
                        "resource_type": "campaign",
                        "resource_id": str(uuid4()),
                        "is_read": False,
                        "created_at": "2025-01-01T00:00:00",
                    }
                ],
                "total": 1,
            }
        )
        app.dependency_overrides[get_service] = lambda: mock_service

        response = await test_client.get(
            f"{self.endpoint_prefix}/notifications",
            params={"organization_id": str(uuid4())},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["title"] == "Campaign Launched"
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_unread_count(self, app: FastAPI, test_client: AsyncClient):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.get_unread_count = AsyncMock(return_value=5)
        app.dependency_overrides[get_service] = lambda: mock_service

        response = await test_client.get(
            f"{self.endpoint_prefix}/notifications/unread-count",
            params={"organization_id": str(uuid4())},
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "data": {"unread_count": 5}}

    @pytest.mark.asyncio
    async def test_mark_read(self, app: FastAPI, test_client: AsyncClient):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.mark_read = AsyncMock()
        app.dependency_overrides[get_service] = lambda: mock_service

        csrf_headers = _setup_csrf(test_client)
        response = await test_client.patch(
            f"{self.endpoint_prefix}/notifications/{uuid4()}/read",
            headers=csrf_headers,
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "data": {"status": "ok"}}

    @pytest.mark.asyncio
    async def test_mark_all_read(self, app: FastAPI, test_client: AsyncClient):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.mark_all_read = AsyncMock(return_value=3)
        app.dependency_overrides[get_service] = lambda: mock_service

        csrf_headers = _setup_csrf(test_client)
        response = await test_client.post(
            f"{self.endpoint_prefix}/notifications/read-all?organization_id={uuid4()}",
            headers=csrf_headers,
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "data": {"marked_read": 3}}

    @pytest.mark.asyncio
    async def test_send_notification(self, app: FastAPI, test_client: AsyncClient):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        notification_id = uuid4()
        mock_notification = MagicMock()
        mock_notification.id = notification_id
        mock_service = MagicMock()
        mock_service.send = AsyncMock(return_value=mock_notification)
        app.dependency_overrides[get_service] = lambda: mock_service

        csrf_headers = _setup_csrf(test_client)
        response = await test_client.post(
            f"{self.endpoint_prefix}/notifications/send",
            json={
                "organization_id": str(uuid4()),
                "user_id": str(uuid4()),
                "type": "campaign_milestone",
                "title": "Campaign Launched",
                "body": "Your campaign is now live",
                "resource_type": "campaign",
                "resource_id": str(uuid4()),
            },
            headers=csrf_headers,
        )

        assert response.status_code == 201
        assert response.json()["data"]["id"] == str(notification_id)

    @pytest.mark.asyncio
    async def test_archive_notification(
        self, app: FastAPI, test_client: AsyncClient
    ):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.archive_notification = AsyncMock()
        app.dependency_overrides[get_service] = lambda: mock_service

        csrf_headers = _setup_csrf(test_client)
        response = await test_client.patch(
            f"{self.endpoint_prefix}/notifications/{uuid4()}/archive",
            headers=csrf_headers,
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "data": {"status": "ok"}}

    @pytest.mark.asyncio
    async def test_search_notifications(
        self, app: FastAPI, test_client: AsyncClient
    ):
        from app.presentation.routes.notifications.notification_hub_routes import (
            get_service,
        )

        mock_service = MagicMock()
        mock_service.search_notifications = AsyncMock(
            return_value=[
                {
                    "id": str(uuid4()),
                    "title": "Found notification",
                }
            ]
        )
        app.dependency_overrides[get_service] = lambda: mock_service

        response = await test_client.get(
            f"{self.endpoint_prefix}/notifications/search",
            params={
                "organization_id": str(uuid4()),
                "q": "campaign",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["title"] == "Found notification"
