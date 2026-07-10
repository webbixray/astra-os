from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.models.workflows.workflow_model import WorkflowModel
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.workflows.workflow_routes import router as workflow_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.fixture(autouse=True)
def _patch_feature_flags():
    with patch(
        "app.presentation.routes.workflows.workflow_routes.require_feature",
        return_value=True,
    ):
        yield


@pytest.mark.asyncio
class TestWorkflowIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(workflow_router, prefix="/api/v1/workflows")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Workflow Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org_with_owner(
        self, integration_session_factory, user_id: UUID,
    ) -> UUID:
        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)
            org = Organization.create(name="Workflow Org", slug="workflow-org")
            org = await org_repo.save(org)
            member = TeamMember.create(
                organization_id=org.id, user_id=user_id, role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    async def test_create_and_get_workflow(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "wf@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/workflows",
            json={
                "organization_id": str(org_id),
                "name": "My Workflow",
                "description": "Test workflow",
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        wf_id = body["id"]
        UUID(wf_id)
        assert body["name"] == "My Workflow"
        assert body["status"] == "draft"
        assert body["organization_id"] == str(org_id)

        resp = await test_client.get(f"/api/v1/workflows/{wf_id}")
        assert resp.status_code == 200, f"get failed: {resp.text}"
        assert resp.json()["name"] == "My Workflow"

    async def test_list_workflows(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "wflist@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        for i in range(3):
            resp = await test_client.post(
                "/api/v1/workflows",
                json={
                    "organization_id": str(org_id),
                    "name": f"WF {i}",
                },
            )
            assert resp.status_code == 201

        resp = await test_client.get(
            "/api/v1/workflows",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200
        wfs = resp.json()
        assert len(wfs) == 3

    async def test_update_workflow(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "wfupdate@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/workflows",
            json={"organization_id": str(org_id), "name": "Original"},
        )
        wf_id = resp.json()["id"]

        resp = await test_client.patch(
            f"/api/v1/workflows/{wf_id}",
            json={
                "name": "Updated",
                "description": "New description",
                "status": "active",
                "nodes": [{"id": "1", "type": "start"}],
                "edges": [{"id": "e1", "source_id": "1", "target_id": "2"}],
            },
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"
        body = resp.json()
        assert body["name"] == "Updated"
        assert body["status"] == "active"

        async with integration_session_factory() as session:
            result = await session.execute(
                select(WorkflowModel).where(WorkflowModel.id == UUID(wf_id)),
            )
            db_wf = result.scalar_one_or_none()
            assert db_wf is not None
            assert db_wf.name == "Updated"

    async def test_get_nonexistent_workflow(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "wfnf@test.com")
        user_id = UUID(auth["user"]["id"])
        await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(f"/api/v1/workflows/{uuid4()}")
        assert resp.status_code == 404

    async def test_workflow_unauthorized(self, test_client):
        resp = await test_client.get("/api/v1/workflows/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403)
