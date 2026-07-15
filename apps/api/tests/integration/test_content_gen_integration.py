from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.content.gen_routes import router as gen_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestContentGenIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(gen_router, prefix="/api/v1")
        app.state.db = integration_session_factory
        register_error_handlers(app)
        return app

    @pytest.fixture
    async def test_client(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def _signup(self, test_client, email: str) -> dict:
        resp = await test_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "Str0ng!Pass", "name": "Content Gen Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org_with_owner(
        self, integration_session_factory, user_id: UUID,
    ) -> UUID:
        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)
            org = Organization.create(name="CG Org", slug="cg-org")
            org = await org_repo.save(org)
            member = TeamMember.create(
                organization_id=org.id, user_id=user_id, role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    async def test_create_and_list_brand_voices(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "bv@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/brand-voices",
            json={
                "organization_id": str(org_id),
                "name": "Professional Voice",
                "tone": "professional",
                "vocabulary": ["innovative", "synergy"],
                "style_guide": "Use clear language",
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        voice_id = body["id"]
        UUID(voice_id)
        assert body["name"] == "Professional Voice"

        resp = await test_client.post(
            "/api/v1/brand-voices",
            json={
                "organization_id": str(org_id),
                "name": "Casual Voice",
                "tone": "casual",
            },
        )
        assert resp.status_code == 201

        resp = await test_client.get(
            "/api/v1/brand-voices",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"list failed: {resp.text}"
        data = resp.json()
        assert data["total"] >= 2
        names = [v["name"] for v in data["data"]]
        assert "Professional Voice" in names
        assert "Casual Voice" in names

    async def test_update_brand_voice(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "bvupdate@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/brand-voices",
            json={
                "organization_id": str(org_id),
                "name": "Original Voice",
                "tone": "professional",
            },
        )
        voice_id = resp.json()["id"]

        resp = await test_client.patch(
            f"/api/v1/brand-voices/{voice_id}",
            params={"organization_id": str(org_id)},
            json={"name": "Updated Voice", "is_active": False},
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"
        assert resp.json()["name"] == "Updated Voice"
        assert resp.json()["is_active"] is False

    async def test_delete_brand_voice(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "bvdel@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/brand-voices",
            json={
                "organization_id": str(org_id),
                "name": "Delete Me",
                "tone": "casual",
            },
        )
        voice_id = resp.json()["id"]

        resp = await test_client.delete(
            f"/api/v1/brand-voices/{voice_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 204

        resp = await test_client.get(
            "/api/v1/brand-voices",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200
        ids = [v["id"] for v in resp.json()["data"]]
        assert voice_id not in ids

    async def test_create_and_get_template(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "tmpl@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/content/templates",
            json={
                "organization_id": str(org_id),
                "name": "Blog Post",
                "content_type": "blog",
                "description": "Standard blog template",
                "sections": [{"name": "intro", "prompt": "Write intro"}],
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        template_id = body["id"]
        UUID(template_id)
        assert body["name"] == "Blog Post"
        assert body["content_type"] == "blog"

        resp = await test_client.get(
            f"/api/v1/content/templates/{template_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"get failed: {resp.text}"
        assert resp.json()["name"] == "Blog Post"

    async def test_list_templates(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "tmpllist@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        for i in range(3):
            resp = await test_client.post(
                "/api/v1/content/templates",
                json={
                    "organization_id": str(org_id),
                    "name": f"Template {i}",
                    "content_type": "social",
                },
            )
            assert resp.status_code == 201

        resp = await test_client.get(
            "/api/v1/content/templates",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    async def test_update_template(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "tmplup@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/content/templates",
            json={
                "organization_id": str(org_id),
                "name": "Original",
                "content_type": "email",
            },
        )
        tmpl_id = resp.json()["id"]

        resp = await test_client.patch(
            f"/api/v1/content/templates/{tmpl_id}",
            params={"organization_id": str(org_id)},
            json={"name": "Updated", "description": "New description"},
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"
        assert resp.json()["name"] == "Updated"

        resp = await test_client.get(
            f"/api/v1/content/templates/{tmpl_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.json()["description"] == "New description"

    async def test_delete_template(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "tmpldel@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/content/templates",
            json={
                "organization_id": str(org_id),
                "name": "Delete Me",
                "content_type": "blog",
            },
        )
        tmpl_id = resp.json()["id"]

        resp = await test_client.delete(
            f"/api/v1/content/templates/{tmpl_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 204

        resp = await test_client.get(
            f"/api/v1/content/templates/{tmpl_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 404

    async def test_get_nonexistent_template(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "tmplnf@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(
            f"/api/v1/content/templates/{uuid4()}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 404

    async def test_update_nonexistent_brand_voice(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "bmerge@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.patch(
            f"/api/v1/brand-voices/{uuid4()}",
            params={"organization_id": str(org_id)},
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404

    async def test_brand_voice_unauthorized(self, test_client):
        resp = await test_client.post(
            "/api/v1/brand-voices",
            json={"organization_id": str(uuid4()), "name": "Hack", "tone": "casual"},
        )
        assert resp.status_code in (401, 403)