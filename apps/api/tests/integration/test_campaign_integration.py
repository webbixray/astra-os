import hashlib
import hmac
import secrets
import time
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.config import config
from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.middleware.csrf import CSRFMiddleware
from app.presentation.routes import auth
from app.presentation.routes.campaigns.campaign_routes import router as campaign_router


def _make_csrf_token() -> tuple[str, str, str]:
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        msg.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    return csrf_token, session_id, csrf_token  # (cookie_value, session_id, header_value)


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestCampaignIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.add_middleware(CSRFMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(campaign_router, prefix="/api/v1/campaigns")
        app.state.db = integration_session_factory
        register_error_handlers(app)
        return app

    @pytest.fixture
    async def test_client(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def _signup_user(self, test_client, email: str) -> dict:
        resp = await test_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "Str0ng!Pass", "name": "Campaign Tester"},
        )
        assert resp.status_code == 201, f"signup failed: {resp.text}"
        return resp.json()

    async def _create_org_and_member(
        self,
        integration_session_factory,
        user_id: UUID,
    ) -> UUID:
        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)

            org = Organization.create(name="Test Org", slug="test-org")
            org = await org_repo.save(org)

            member = TeamMember.create(
                organization_id=org.id,
                user_id=user_id,
                role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    async def _set_auth_header(self, test_client, token: str):
        test_client.headers["Authorization"] = f"Bearer {token}"

    async def _set_csrf(self, test_client):
        csrf_cookie, session_id, csrf_header = _make_csrf_token()
        test_client.cookies.set("astra_csrf", csrf_cookie)
        test_client.cookies.set("astra_session", session_id)
        test_client.headers["X-CSRF-Token"] = csrf_header

    async def test_create_and_retrieve_campaign(self, test_client, integration_session_factory):
        # ── Setup: user + org + member ──────────────────────────────────
        auth_resp = await self._signup_user(test_client, "campaign@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)

        await self._set_auth_header(test_client, auth_resp["access_token"])
        await self._set_csrf(test_client)

        # ── Create campaign ─────────────────────────────────────────────
        resp = await test_client.post(
            "/api/v1/campaigns",
            json={
                "name": "Test Campaign",
                "description": "Integration test campaign",
                "budget_amount": 5000.0,
                "budget_currency": "USD",
                "channels": ["social", "email"],
                "objective": "awareness",
                "organization_id": str(org_id),
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        campaign_id = body["id"]
        UUID(campaign_id)
        assert body["name"] == "Test Campaign"
        assert body["status"] == "draft"
        assert body["organization_id"] == str(org_id)

        # ── Get by id ───────────────────────────────────────────────────
        resp = await test_client.get(f"/api/v1/campaigns/{campaign_id}")
        assert resp.status_code == 200, f"get failed: {resp.text}"
        body = resp.json()
        assert body["name"] == "Test Campaign"
        assert body["organization_id"] == str(org_id)
        assert body["id"] == campaign_id

        # ── List ────────────────────────────────────────────────────────
        resp = await test_client.get(
            "/api/v1/campaigns",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"list failed: {resp.text}"
        body = resp.json()
        assert body["total"] >= 1
        ids = [item["id"] for item in body["data"]]
        assert campaign_id in ids

        # ── Update ──────────────────────────────────────────────────────
        resp = await test_client.patch(
            f"/api/v1/campaigns/{campaign_id}",
            json={"name": "Updated Campaign", "description": "Updated description"},
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"
        body = resp.json()
        assert body["name"] == "Updated Campaign"
        assert body["description"] == "Updated description"

        # ── Verify in DB directly ───────────────────────────────────────
        async with integration_session_factory() as session:
            result = await session.execute(
                select(CampaignModel).where(CampaignModel.id == UUID(campaign_id)),
            )
            db_campaign = result.scalar_one_or_none()
            assert db_campaign is not None
            assert db_campaign.name == "Updated Campaign"

    async def test_list_empty(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "empty@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)

        await self._set_auth_header(test_client, auth_resp["access_token"])
        await self._set_csrf(test_client)

        resp = await test_client.get(
            "/api/v1/campaigns",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []

    async def test_create_campaign_missing_org_id(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "missing@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        await self._create_org_and_member(integration_session_factory, user_id)

        await self._set_auth_header(test_client, auth_resp["access_token"])
        await self._set_csrf(test_client)

        resp = await test_client.post(
            "/api/v1/campaigns",
            json={"name": "No Org", "organization_id": str(uuid4())},
        )
        assert resp.status_code in (403, 404), (
            f"expected forbidden/not-found, got {resp.status_code}"
        )

    async def test_get_nonexistent_campaign(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "nonexist@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        await self._create_org_and_member(integration_session_factory, user_id)

        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.get(f"/api/v1/campaigns/{uuid4()}")
        assert resp.status_code == 404, f"expected 404, got {resp.status_code}"
