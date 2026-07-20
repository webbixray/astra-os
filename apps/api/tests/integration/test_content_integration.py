from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.models.content.content_model import ContentModel
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.content.content_routes import router as content_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestContentIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(content_router, prefix="/api/v1/content")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Content Tester"},
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

            org = Organization.create(name="Content Org", slug="content-org")
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

    async def test_create_and_get_content(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "content@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.post(
            "/api/v1/content",
            json={
                "organization_id": str(org_id),
                "title": "Test Blog Post",
                "content_type": "blog",
                "body": "Hello world",
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        content_id = body["id"]
        UUID(content_id)
        assert body["title"] == "Test Blog Post"
        assert body["content_type"] == "blog"
        assert body["status"] == "draft"
        assert body["organization_id"] == str(org_id)

        resp = await test_client.get(f"/api/v1/content/{content_id}")
        assert resp.status_code == 200, f"get failed: {resp.text}"
        body = resp.json()
        assert body["title"] == "Test Blog Post"
        assert body["id"] == content_id

    async def test_list_content(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "listcontent@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        for i in range(3):
            resp = await test_client.post(
                "/api/v1/content",
                json={
                    "organization_id": str(org_id),
                    "title": f"Post {i}",
                    "content_type": "blog",
                },
            )
            assert resp.status_code == 201

        resp = await test_client.get(
            "/api/v1/content",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"list failed: {resp.text}"
        body = resp.json()
        assert body["total"] == 3
        assert len(body["data"]) == 3

    async def test_update_content(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "updatecontent@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.post(
            "/api/v1/content",
            json={
                "organization_id": str(org_id),
                "title": "Original",
                "content_type": "blog",
                "body": "Original body",
            },
        )
        content_id = resp.json()["id"]

        resp = await test_client.patch(
            f"/api/v1/content/{content_id}",
            json={"title": "Updated", "body": "Updated body", "status": "review"},
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"
        body = resp.json()
        assert body["title"] == "Updated"
        assert body["body"] == "Updated body"
        assert body["status"] == "review"

        async with integration_session_factory() as session:
            result = await session.execute(
                select(ContentModel).where(ContentModel.id == UUID(content_id)),
            )
            db_content = result.scalar_one_or_none()
            assert db_content is not None
            assert db_content.title == "Updated"
            assert db_content.status == "review"

    async def test_create_content_missing_org(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "missingorg@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.post(
            "/api/v1/content",
            json={
                "organization_id": str(uuid4()),
                "title": "No Org",
                "content_type": "blog",
            },
        )
        assert resp.status_code in (403, 404), (
            f"expected forbidden/not-found, got {resp.status_code}"
        )

    async def test_get_nonexistent_content(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "nonexistcontent@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.get(f"/api/v1/content/{uuid4()}")
        assert resp.status_code == 404, f"expected 404, got {resp.status_code}"

    async def test_create_content_invalid_type(self, test_client, integration_session_factory):
        auth_resp = await self._signup_user(test_client, "invalidtype@test.com")
        user_id = UUID(auth_resp["user"]["id"])
        org_id = await self._create_org_and_member(integration_session_factory, user_id)
        await self._set_auth_header(test_client, auth_resp["access_token"])

        resp = await test_client.post(
            "/api/v1/content",
            json={
                "organization_id": str(org_id),
                "title": "Bad Type",
                "content_type": "nonexistent_type",
            },
        )
        assert resp.status_code == 422, f"expected 422, got {resp.status_code}"

    async def test_content_unauthorized(self, test_client):
        resp = await test_client.get("/api/v1/content/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403), f"expected unauthorized, got {resp.status_code}"
