from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.main import create_app
from app.presentation.dependencies import (
    get_create_org_use_case,
    get_create_user_use_case,
    get_get_org_use_case,
    get_get_user_use_case,
    get_list_orgs_use_case,
    get_update_org_use_case,
    get_update_user_use_case,
    get_user_repo,
)
from app.presentation.middleware.auth import require_user_id


def _mock_org(**kwargs) -> MagicMock:
    org = MagicMock()
    org.id = kwargs.get("id", uuid4())
    org.name = kwargs.get("name", "Test Org")
    org.slug = kwargs.get("slug", "test-org")
    org.plan_tier = kwargs.get("plan_tier", "free")
    org.settings = kwargs.get("settings", {})
    org.created_at = kwargs.get("created_at", datetime.now())
    org.updated_at = kwargs.get("updated_at", datetime.now())
    return org


def _mock_user(**kwargs) -> MagicMock:
    user = MagicMock()
    user.id = kwargs.get("id", uuid4())
    user.email = kwargs.get("email", "test@test.com")
    user.name = kwargs.get("name", "Test User")
    user.avatar_url = kwargs.get("avatar_url")
    user.created_at = kwargs.get("created_at", datetime.now())
    user.updated_at = kwargs.get("updated_at", datetime.now())
    return user


_MOCK_USER_ID = uuid4()


@pytest.fixture
def app() -> FastAPI:
    a = create_app()

    mock_member = MagicMock()
    mock_member.role = "owner"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_member)

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_session_factory = MagicMock(return_value=mock_session)
    a.state.db = mock_session_factory

    a.dependency_overrides[require_user_id] = lambda: _MOCK_USER_ID

    yield a
    a.dependency_overrides.clear()


@pytest.fixture
async def test_client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


class TestHealthRoute:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, app: FastAPI, test_client: AsyncClient):
        with patch("app.infrastructure.cache.redis.RedisCache") as mock_redis:
            mock_cache = AsyncMock()
            mock_cache.connect = AsyncMock()
            mock_cache.client = AsyncMock()
            mock_cache.client.ping = AsyncMock(return_value=True)
            mock_cache.disconnect = AsyncMock()
            mock_redis.return_value = mock_cache

            response = await test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data


class TestAuthRoutes:
    @pytest.mark.asyncio
    async def test_signup_success(self, app: FastAPI, test_client: AsyncClient):
        mock_repo = MagicMock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock(side_effect=lambda user: user)
        app.dependency_overrides[get_user_repo] = lambda: mock_repo

        response = await test_client.post(
            "/api/v1/auth/signup",
            json={"email": "test@test.com", "password": "P@ssword123!", "name": "Test"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["user"]["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, app: FastAPI, test_client: AsyncClient):
        mock_repo = MagicMock()
        mock_repo.find_by_email = AsyncMock(return_value=MagicMock())
        app.dependency_overrides[get_user_repo] = lambda: mock_repo

        response = await test_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@test.com",
                "password": "P@ssword123!",
                "name": "Test",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signin_success(self, app: FastAPI, test_client: AsyncClient):
        mock_repo = MagicMock()
        mock_repo.find_by_email = AsyncMock(
            return_value=_mock_user(password_hash="", is_active=True)
        )
        app.dependency_overrides[get_user_repo] = lambda: mock_repo

        with patch(
            "app.application.use_cases.auth_use_cases.verify_password",
            return_value=True,
        ):
            response = await test_client.post(
                "/api/v1/auth/signin",
                json={"email": "test@test.com", "password": "P@ssword123!"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_signin_wrong_password(self, app: FastAPI, test_client: AsyncClient):
        mock_repo = MagicMock()
        mock_repo.find_by_email = AsyncMock(
            return_value=_mock_user(password_hash="wrong_hash", is_active=True)
        )
        app.dependency_overrides[get_user_repo] = lambda: mock_repo

        with patch(
            "app.application.use_cases.auth_use_cases.verify_password",
            return_value=False,
        ):
            response = await test_client.post(
                "/api/v1/auth/signin",
                json={"email": "test@test.com", "password": "P@ssword123!"},
            )

        assert response.status_code == 422


class TestUserRoutes:
    async def _setup(self, test_client):
        import hashlib
        import hmac
        import secrets

        from app.config import config

        secret = config.secret_key
        session_id = secrets.token_urlsafe(16)
        import time

        timestamp = int(time.time())
        msg = f"{session_id}:{timestamp}"
        signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
        csrf_token = f"{timestamp}:{signature}"
        test_client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
        return {"X-CSRF-Token": csrf_token}

    @pytest.mark.asyncio
    async def test_create_user_success(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_user(id=uuid4(), email="new@test.com", name="New User")
        )
        app.dependency_overrides[get_create_user_use_case] = lambda: mock_use_case

        csrf = await self._setup(test_client)
        response = await test_client.post(
            "/api/v1/users",
            json={"email": "new@test.com", "name": "New User"},
            headers=csrf,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["email"] == "new@test.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_user(id=_MOCK_USER_ID, email="test@test.com", name="Test User")
        )
        app.dependency_overrides[get_get_user_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/users/{_MOCK_USER_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(_MOCK_USER_ID)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("User", str(_MOCK_USER_ID))
        )
        app.dependency_overrides[get_get_user_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/users/{_MOCK_USER_ID}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_user(id=_MOCK_USER_ID, email="test@test.com", name="Updated Name")
        )
        app.dependency_overrides[get_update_user_use_case] = lambda: mock_use_case

        csrf = await self._setup(test_client)
        response = await test_client.patch(
            f"/api/v1/users/{_MOCK_USER_ID}",
            json={"name": "Updated Name"},
            headers=csrf,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Name"


class TestOrganizationRoutes:
    async def _setup(self, test_client):
        import hashlib
        import hmac
        import secrets

        from app.config import config

        secret = config.secret_key
        session_id = secrets.token_urlsafe(16)
        import time

        timestamp = int(time.time())
        msg = f"{session_id}:{timestamp}"
        signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
        csrf_token = f"{timestamp}:{signature}"
        test_client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
        return {"X-CSRF-Token": csrf_token}

    @pytest.mark.asyncio
    async def test_create_organization(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_org(id=org_id, name="Test Org", slug="test-org")
        )
        app.dependency_overrides[get_create_org_use_case] = lambda: mock_use_case

        csrf = await self._setup(test_client)
        response = await test_client.post(
            "/api/v1/organizations",
            json={"name": "Test Org", "slug": "test-org"},
            headers=csrf,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "Test Org"

    @pytest.mark.asyncio
    async def test_get_my_organizations(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=[_mock_org(id=uuid4(), name="Org 1", slug="org-1")]
        )
        app.dependency_overrides[get_list_orgs_use_case] = lambda: mock_use_case

        response = await test_client.get("/api/v1/organizations/my")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_org(id=org_id, name="Test Org", slug="test-org")
        )
        app.dependency_overrides[get_get_org_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/organizations/{org_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(org_id)

    @pytest.mark.asyncio
    async def test_update_organization(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_mock_org(id=org_id, name="Updated Org", slug="updated-org")
        )
        app.dependency_overrides[get_update_org_use_case] = lambda: mock_use_case

        csrf = await self._setup(test_client)
        response = await test_client.patch(
            f"/api/v1/organizations/{org_id}",
            json={"name": "Updated Org"},
            headers=csrf,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Org"
