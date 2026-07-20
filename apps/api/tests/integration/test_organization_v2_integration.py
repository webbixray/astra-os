from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.infrastructure.auth.jwt import RefreshTokenStore
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.organizations_v2 import router as org_v2_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


def _make_org(integration_session_factory):
    """Create an org and return (org_id, user_id, access_token)."""


@pytest.mark.asyncio
class TestOrganizationV2Integration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(org_v2_router, prefix="/api/v1")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Org V2 Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org(
        self,
        integration_session_factory,
        user_id: UUID,
        name: str = "Test Org",
        slug: str = "test-org",
    ) -> UUID:
        from app.domain.entities.organization import Organization
        from app.domain.entities.team_member import TeamMember
        from app.infrastructure.db.repositories.organization_repository import (
            OrganizationRepositoryImpl,
        )
        from app.infrastructure.db.repositories.team_member_repository import (
            TeamMemberRepositoryImpl,
        )

        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)
            org = Organization.create(name=name, slug=slug)
            org = await org_repo.save(org)
            member = TeamMember.create(
                organization_id=org.id,
                user_id=user_id,
                role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    async def test_create_sub_org(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "suborg@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            f"/api/v1/organizations/{org_id}/sub-orgs",
            json={"name": "Sub Org", "slug": "sub-org"},
        )
        assert resp.status_code == 201, f"create sub-org failed: {resp.text}"
        body = resp.json()
        assert body["name"] == "Sub Org"
        assert body["slug"] == "sub-org"
        assert body["parent_org_id"] == str(org_id)
        UUID(body["id"])

    async def test_get_org_tree(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "orgtree@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        await test_client.post(
            f"/api/v1/organizations/{org_id}/sub-orgs",
            json={"name": "Child", "slug": "child-org"},
        )

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/tree")
        assert resp.status_code == 200, f"tree failed: {resp.text}"
        body = resp.json()
        assert body["id"] == str(org_id)
        assert len(body["children"]) == 1
        assert body["children"][0]["name"] == "Child"

    async def test_invite_and_accept_flow(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "inviter@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        second = await self._signup(test_client, "invitee@test.com")
        UUID(second["user"]["id"])

        resp = await test_client.post(
            f"/api/v1/organizations/{org_id}/invitations",
            json={"email": "invitee@test.com", "role": "member"},
        )
        assert resp.status_code == 201, f"invite failed: {resp.text}"
        inv_body = resp.json()
        invitation_id = inv_body["id"]
        assert inv_body["email"] == "invitee@test.com"
        assert inv_body["status"] == "pending"

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/invitations")
        assert resp.status_code == 200
        invitations = resp.json()
        assert len(invitations) >= 1
        assert invitations[0]["email"] == "invitee@test.com"

        test_client.headers["Authorization"] = f"Bearer {second['access_token']}"
        resp = await test_client.post(f"/api/v1/invitations/{invitation_id}/accept")
        assert resp.status_code == 200, f"accept failed: {resp.text}"
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["role"] == "member"

    async def test_reject_invitation(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "rejector@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        rejectee = await self._signup(test_client, "rejectee@test.com")

        resp = await test_client.post(
            f"/api/v1/organizations/{org_id}/invitations",
            json={"email": "rejectee@test.com", "role": "member"},
        )
        invitation_id = resp.json()["id"]

        test_client.headers["Authorization"] = f"Bearer {rejectee['access_token']}"
        resp = await test_client.post(f"/api/v1/invitations/{invitation_id}/reject")
        assert resp.status_code == 200, f"reject failed: {resp.text}"
        assert resp.json()["status"] == "rejected"

    async def test_list_members(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "listmembers@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/members")
        assert resp.status_code == 200, f"list members failed: {resp.text}"
        members = resp.json()
        assert len(members) >= 1
        assert members[0]["email"] == "listmembers@test.com"
        assert members[0]["role"] == "owner"

    async def test_change_member_role(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "changerole@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        from app.domain.entities.team_member import TeamMember
        from app.infrastructure.db.repositories.team_member_repository import (
            TeamMemberRepositoryImpl,
        )

        target = await self._signup(test_client, "changerole_target@test.com")
        target_id = UUID(target["user"]["id"])
        async with integration_session_factory() as session:
            member_repo = TeamMemberRepositoryImpl(session)
            member = TeamMember.create(
                organization_id=org_id,
                user_id=target_id,
                role="member",
            )
            member = await member_repo.save(member)
            member_id = member.id
            await session.commit()

        resp = await test_client.patch(
            f"/api/v1/organizations/{org_id}/members/{member_id}/role",
            json={"role": "admin"},
        )
        assert resp.status_code == 200, f"change role failed: {resp.text}"
        assert resp.json()["role"] == "admin"

    async def test_feature_flags(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "features@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/features")
        assert resp.status_code == 200
        assert resp.json() == []

        resp = await test_client.put(
            f"/api/v1/organizations/{org_id}/features",
            json={"feature_key": "dark_mode", "enabled": True},
        )
        assert resp.status_code == 200, f"set flag failed: {resp.text}"
        flag = resp.json()
        assert flag["feature_key"] == "dark_mode"
        assert flag["enabled"] is True
        flag_id = flag["id"]

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/features")
        flags = resp.json()
        assert len(flags) == 1
        assert flags[0]["feature_key"] == "dark_mode"

        resp = await test_client.delete(
            f"/api/v1/organizations/{org_id}/features/{flag_id}",
        )
        assert resp.status_code == 204

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/features")
        assert resp.json() == []

    async def test_billing_plan(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "billing@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/billing")
        assert resp.status_code == 200, f"get billing failed: {resp.text}"
        plan = resp.json()
        assert plan["plan_tier"] == "free"
        assert "current_period_start" in plan
        assert "current_period_end" in plan

        resp = await test_client.put(
            f"/api/v1/organizations/{org_id}/billing",
            json={"plan_tier": "professional"},
        )
        assert resp.status_code == 200, f"change plan failed: {resp.text}"
        assert resp.json()["plan_tier"] == "professional"

    async def test_permissions(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "perms@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(
            f"/api/v1/organizations/{org_id}/check-permission/org:read",
        )
        assert resp.status_code == 200
        assert resp.json() == {"has_permission": True}

        resp = await test_client.get(
            f"/api/v1/organizations/{org_id}/check-permission/nonexistent",
        )
        assert resp.json() == {"has_permission": False}

    async def test_usage(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "usage@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(f"/api/v1/organizations/{org_id}/usage")
        assert resp.status_code == 200, f"usage failed: {resp.text}"
        usage = resp.json()
        assert "usage" in usage
        assert "limits" in usage
        assert usage["plan_tier"] == "free"

        resp = await test_client.get(
            f"/api/v1/organizations/{org_id}/usage/api_requests/trend",
            params={"days": 7},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_set_parent_org(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "setparent@test.com")
        user_id = UUID(auth["user"]["id"])
        org_a = await self._create_org(
            integration_session_factory,
            user_id,
            name="Org A",
            slug="org-a",
        )
        org_b = await self._create_org(
            integration_session_factory,
            user_id,
            name="Org B",
            slug="org-b",
        )
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            f"/api/v1/organizations/{org_b}/parent",
            json={"parent_org_id": str(org_a)},
        )
        assert resp.status_code == 200, f"set parent failed: {resp.text}"
        assert resp.json()["parent_org_id"] == str(org_a)
