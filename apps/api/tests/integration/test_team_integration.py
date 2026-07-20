from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.team import router as team_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestTeamIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(team_router, prefix="/api/v1")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Team Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org_with_owner(
        self,
        integration_session_factory,
        user_id: UUID,
        name: str = "Team Org",
        slug: str = "team-org",
    ) -> UUID:
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

    async def test_invite_existing_user(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "teamowner@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        await self._signup(test_client, "teammember@test.com")

        resp = await test_client.post(
            "/api/v1/teams/invite",
            json={
                "organization_id": str(org_id),
                "email": "teammember@test.com",
                "role": "member",
            },
        )
        assert resp.status_code == 201, f"invite failed: {resp.text}"
        body = resp.json()
        assert body["status"] == "invited"
        assert body["role"] == "member"

    async def test_list_members(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "listteams@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        second = await self._signup(test_client, "secondteam@test.com")
        second_id = UUID(second["user"]["id"])
        async with integration_session_factory() as session:
            member_repo = TeamMemberRepositoryImpl(session)
            member = TeamMember.create(
                organization_id=org_id,
                user_id=second_id,
                role="member",
            )
            await member_repo.save(member)
            await session.commit()

        resp = await test_client.get(
            "/api/v1/teams/members",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"list failed: {resp.text}"
        body = resp.json()
        assert body["total"] == 2
        emails = [m["email"] for m in body["data"]]
        assert "listteams@test.com" in emails
        assert "secondteam@test.com" in emails

    async def test_update_member_role(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "updaterole@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        target = await self._signup(test_client, "targetrole@test.com")
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
            f"/api/v1/teams/members/{member_id}/role",
            json={"role": "admin"},
        )
        assert resp.status_code == 200, f"update role failed: {resp.text}"
        assert resp.json()["role"] == "admin"

        async with integration_session_factory() as session:
            result = await session.execute(
                select(TeamMemberModel).where(TeamMemberModel.id == member_id),
            )
            db_member = result.scalar_one()
            assert db_member.role == "admin"

    async def test_remove_member(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "removeteam@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        target = await self._signup(test_client, "removetarget@test.com")
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

        resp = await test_client.delete(f"/api/v1/teams/members/{member_id}")
        assert resp.status_code == 204, f"remove failed: {resp.text}"

        async with integration_session_factory() as session:
            result = await session.execute(
                select(TeamMemberModel).where(TeamMemberModel.id == member_id),
            )
            assert result.scalar_one_or_none() is None

    async def test_invite_nonexistent_user(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "invitenonexist@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        resp = await test_client.post(
            "/api/v1/teams/invite",
            json={
                "organization_id": str(org_id),
                "email": "doesnotexist@test.com",
                "role": "member",
            },
        )
        assert resp.status_code == 404, f"expected 404, got {resp.status_code}"

    async def test_invite_duplicate_member(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "invitedupe@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        target = await self._signup(test_client, "dupetarget@test.com")
        target_id = UUID(target["user"]["id"])
        async with integration_session_factory() as session:
            member_repo = TeamMemberRepositoryImpl(session)
            member = TeamMember.create(
                organization_id=org_id,
                user_id=target_id,
                role="member",
            )
            await member_repo.save(member)
            await session.commit()

        resp = await test_client.post(
            "/api/v1/teams/invite",
            json={
                "organization_id": str(org_id),
                "email": "dupetarget@test.com",
                "role": "member",
            },
        )
        assert resp.status_code == 409, f"expected 409, got {resp.status_code}"

    async def test_team_unauthorized(self, test_client):
        resp = await test_client.get(
            "/api/v1/teams/members",
            params={"organization_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert resp.status_code in (401, 403), f"expected unauthorized, got {resp.status_code}"

    async def test_cannot_remove_self(self, test_client, integration_session_factory):
        owner = await self._signup(test_client, "removeself@test.com")
        owner_id = UUID(owner["user"]["id"])
        org_id = await self._create_org_with_owner(
            integration_session_factory,
            owner_id,
        )
        test_client.headers["Authorization"] = f"Bearer {owner['access_token']}"

        async with integration_session_factory() as session:
            member_repo = TeamMemberRepositoryImpl(session)
            members = await member_repo.find_by_organization(org_id)
            owner_member_id = members[0].id

        resp = await test_client.delete(f"/api/v1/teams/members/{owner_member_id}")
        assert resp.status_code == 400, f"expected 400, got {resp.status_code}"
