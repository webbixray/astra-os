from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.infrastructure.auth.jwt import RefreshTokenStore
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestAuthIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.state.db = integration_session_factory
        register_error_handlers(app)
        return app

    @pytest.fixture
    async def test_client(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_full_auth_flow(self, test_client):
        email = "integration@test.com"
        password = "Str0ng!Pass"
        name = "Integration Test"

        # ── Signup ──────────────────────────────────────────────────────
        resp = await test_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": password, "name": name},
        )
        assert resp.status_code == 201, f"signup failed: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["user"]["email"] == email
        assert body["user"]["name"] == name
        user_id = body["user"]["id"]
        UUID(user_id)  # validate UUID
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]

        # ── Signin with same credentials ────────────────────────────────
        resp = await test_client.post(
            "/api/v1/auth/signin",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200, f"signin failed: {resp.text}"
        body = resp.json()
        assert body["user"]["id"] == user_id
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]

        # ── Get current user (GET /me) ──────────────────────────────────
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200, f"/me failed: {resp.text}"
        body = resp.json()
        assert body["id"] == user_id
        assert body["email"] == email

        # ── Refresh token ───────────────────────────────────────────────
        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, f"refresh failed: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        new_access = body["access_token"]
        new_refresh = body["refresh_token"]

        # ── New access token works ──────────────────────────────────────
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert resp.status_code == 200

        # ── Logout ──────────────────────────────────────────────────────
        resp = await test_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh},
        )
        assert resp.status_code == 200, f"logout failed: {resp.text}"
        assert resp.json()["message"] == "Logged out successfully"

        # ── Old access token still works (not expired, just refresh revoked) ─
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert resp.status_code == 200

        # ── Used refresh token is revoked ───────────────────────────────
        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert resp.status_code == 422, "expected revoked refresh to be rejected"

    async def test_signup_duplicate_email(self, test_client):
        email = "dupe@test.com"
        payload = {"email": email, "password": "Str0ng!Pass", "name": "Dupe"}
        resp = await test_client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code == 201

        resp = await test_client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code in (409, 422), f"expected duplicate rejection, got {resp.status_code}"

    async def test_signup_weak_password(self, test_client):
        payload = {"email": "weak@test.com", "password": "short", "name": "Weak"}
        resp = await test_client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code in (400, 422), f"expected weak password rejection, got {resp.status_code}"

    async def test_signin_wrong_password(self, test_client):
        email = "wrongpw@test.com"
        await test_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "Str0ng!Pass", "name": "Wrong"},
        )
        resp = await test_client.post(
            "/api/v1/auth/signin",
            json={"email": email, "password": "WrongPassword1!"},
        )
        assert resp.status_code in (400, 401, 422), f"expected wrong password rejection, got {resp.status_code}"

    async def test_me_unauthorized(self, test_client):
        resp = await test_client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403), f"expected unauthorized, got {resp.status_code}"
