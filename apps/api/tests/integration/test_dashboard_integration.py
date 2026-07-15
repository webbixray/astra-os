from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.models.dashboards.dashboard_model import (
    DashboardModel,
    DashboardWidgetModel,
)
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.dashboards.dashboard_routes import router as dashboard_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestDashboardIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(dashboard_router, prefix="/api/v1")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Dashboard Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org_with_owner(
        self, integration_session_factory, user_id: UUID, name: str = "Dash Org",
        slug: str = "dash-org",
    ) -> UUID:
        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)
            org = Organization.create(name=name, slug=slug)
            org = await org_repo.save(org)
            member = TeamMember.create(
                organization_id=org.id, user_id=user_id, role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    async def test_create_dashboard(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "createdash@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/dashboards",
            json={
                "organization_id": str(org_id),
                "name": "My Dashboard",
                "description": "Test dashboard",
            },
        )
        assert resp.status_code == 201, f"create failed: {resp.text}"
        body = resp.json()
        dash_id = body["id"]
        UUID(dash_id)
        assert body["name"] == "My Dashboard"
        assert body["description"] == "Test dashboard"

    async def test_list_dashboards(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "listdash@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        for i in range(3):
            resp = await test_client.post(
                "/api/v1/dashboards",
                json={
                    "organization_id": str(org_id),
                    "name": f"Dash {i}",
                },
            )
            assert resp.status_code == 201

        resp = await test_client.get(
            "/api/v1/dashboards",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"list failed: {resp.text}"
        dashes = resp.json()
        assert len(dashes) >= 3
        names = [d["name"] for d in dashes]
        assert "Dash 0" in names
        assert "Dash 1" in names
        assert "Dash 2" in names

    async def test_get_dashboard(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "getdash@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/dashboards",
            json={"organization_id": str(org_id), "name": "Get Me"},
        )
        dash_id = resp.json()["id"]

        resp = await test_client.get(
            f"/api/v1/dashboards/{dash_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 200, f"get failed: {resp.text}"
        assert resp.json()["name"] == "Get Me"

    async def test_delete_dashboard(self, test_client, integration_session_factory):
            auth = await self._signup(test_client, "deldash@test.com")
            user_id = UUID(auth["user"]["id"])
            org_id = await self._create_org_with_owner(integration_session_factory, user_id)
            test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

            resp = await test_client.post(
                "/api/v1/dashboards",
                json={"organization_id": str(org_id), "name": "Delete Me"},
            )
            dash_id = resp.json()["id"]

            resp = await test_client.delete(
                f"/api/v1/dashboards/{dash_id}",
                params={"organization_id": str(org_id)},
            )
            assert resp.status_code == 204

            async with integration_session_factory() as session:
                result = await session.execute(
                    select(DashboardModel).where(DashboardModel.id == UUID(dash_id)),
                )
                assert result.scalar_one_or_none() is None

    async def test_widget_full_flow(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "widgets@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/dashboards",
            json={"organization_id": str(org_id), "name": "Widget Dash"},
        )
        dash_id = resp.json()["id"]

        resp = await test_client.post(
            f"/api/v1/dashboards/{dash_id}/widgets",
            params={"organization_id": str(org_id)},
            json={
                "widget_type": "kpi_card",
                "title": "Revenue",
                "pos_x": 0,
                "pos_y": 0,
                "width": 2,
                "height": 1,
                "config": {"metric": "ad_spend"},
            },
        )
        assert resp.status_code == 201, f"add widget failed: {resp.text}"
        widget = resp.json()
        widget_id = widget["id"]
        UUID(widget_id)
        assert widget["widget_type"] == "kpi_card"
        assert widget["title"] == "Revenue"
        assert widget["config"] == {"metric": "ad_spend"}

        resp = await test_client.put(
            f"/api/v1/dashboards/widgets/{widget_id}",
            params={"organization_id": str(org_id)},
            json={"title": "Updated Revenue", "width": 3},
        )
        assert resp.status_code == 200, f"update widget failed: {resp.text}"
        assert resp.json()["title"] == "Updated Revenue"
        assert resp.json()["width"] == 3

        async with integration_session_factory() as session:
            result = await session.execute(
                select(DashboardWidgetModel).where(
                    DashboardWidgetModel.id == UUID(widget_id),
                ),
            )
            db_widget = result.scalar_one()
            assert db_widget.title == "Updated Revenue"
            assert db_widget.width == 3

        resp = await test_client.delete(
            f"/api/v1/dashboards/widgets/{widget_id}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 204

        async with integration_session_factory() as session:
            result = await session.execute(
                select(DashboardWidgetModel).where(
                    DashboardWidgetModel.id == UUID(widget_id),
                ),
            )
            assert result.scalar_one_or_none() is None

    async def test_get_nonexistent_dashboard(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "notfounddash@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(
            f"/api/v1/dashboards/{uuid4()}",
            params={"organization_id": str(org_id)},
        )
        assert resp.status_code == 404

    async def test_get_nonexistent_widget(self, test_client, integration_session_factory):
        auth = await self._signup(test_client, "notfoundwidget@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.put(
            f"/api/v1/dashboards/widgets/{uuid4()}",
            params={"organization_id": str(org_id)},
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    async def test_dashboard_unauthorized(self, test_client):
        resp = await test_client.get("/api/v1/dashboards/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403), f"expected unauthorized, got {resp.status_code}"
