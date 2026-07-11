from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.routes import auth
from app.presentation.routes.knowledge.knowledge_routes import router as knowledge_router


@pytest.fixture(autouse=True)
def _clear_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest.mark.asyncio
class TestKnowledgeIntegration:
    @pytest.fixture
    def app(self, integration_session_factory):
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        app.include_router(auth.router, prefix="/api/v1/auth")
        app.include_router(knowledge_router, prefix="/api/v1")
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
            json={"email": email, "password": "Str0ng!Pass", "name": "Knowledge Tester"},
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_org_with_owner(
        self, integration_session_factory, user_id: UUID,
    ) -> UUID:
        async with integration_session_factory() as session:
            org_repo = OrganizationRepositoryImpl(session)
            member_repo = TeamMemberRepositoryImpl(session)
            org = Organization.create(name="Know Org", slug="know-org")
            org = await org_repo.save(org)
            member = TeamMember.create(
                organization_id=org.id, user_id=user_id, role="owner",
            )
            await member_repo.save(member)
            await session.commit()
            return org.id

    @patch("app.presentation.routes.knowledge.knowledge_routes.GraphStore", autospec=True)
    async def test_create_node(self, mock_graph_store_cls, test_client, integration_session_factory):
        mock_store = AsyncMock(spec=GraphStore)
        mock_store.upsert_node = AsyncMock()
        mock_graph_store_cls.return_value = mock_store

        auth = await self._signup(test_client, "knode@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/knowledge/nodes",
            json={
                "organization_id": str(org_id),
                "type": "concept",
                "name": "Machine Learning",
                "description": "AI subfield",
            },
        )
        assert resp.status_code == 200, f"create failed: {resp.text}"
        body = resp.json()
        assert body["name"] == "Machine Learning"
        assert body["type"] == "concept"
        assert UUID(body["id"])
        mock_store.upsert_node.assert_called_once()



    @patch("app.presentation.routes.knowledge.knowledge_routes.GraphStore", autospec=True)
    async def test_search(self, mock_graph_store_cls, test_client, integration_session_factory):
        mock_store = AsyncMock(spec=GraphStore)
        mock_store.search_similar = AsyncMock(return_value=[
            {"id": str(uuid4()), "type": "concept", "name": "AI", "similarity": 0.95},
        ])
        mock_graph_store_cls.return_value = mock_store

        auth = await self._signup(test_client, "ksearch@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/knowledge/search",
            json={
                "organization_id": str(org_id),
                "query": "artificial intelligence",
                "limit": 5,
            },
        )
        assert resp.status_code == 200, f"search failed: {resp.text}"
        assert len(resp.json()) == 1

    @patch("app.presentation.routes.knowledge.knowledge_routes.GraphStore", autospec=True)
    async def test_memory_remember_and_recall(self, mock_graph_store_cls, test_client, integration_session_factory):
        mock_store = AsyncMock(spec=GraphStore)
        mock_store.upsert_memory = AsyncMock()
        mock_store.search_memories = AsyncMock(return_value=[
            {"id": str(uuid4()), "key": "user_pref", "value": "dark_mode", "similarity": 0.9},
        ])
        mock_graph_store_cls.return_value = mock_store

        auth = await self._signup(test_client, "kmem@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.post(
            "/api/v1/knowledge/memory/remember",
            json={
                "organization_id": str(org_id),
                "user_id": str(user_id),
                "key": "user_pref",
                "value": "dark_mode",
            },
        )
        assert resp.status_code == 200, f"remember failed: {resp.text}"

        resp = await test_client.post(
            "/api/v1/knowledge/memory/recall",
            json={
                "organization_id": str(org_id),
                "user_id": str(user_id),
                "query": "preferences",
            },
        )
        assert resp.status_code == 200, f"recall failed: {resp.text}"
        results = resp.json()
        assert len(results) == 1
        assert results[0]["key"] == "user_pref"

    @patch("app.presentation.routes.knowledge.knowledge_routes.KnowledgeGraphService", autospec=True)
    async def test_get_node_relations(self, mock_service_cls, test_client, integration_session_factory):
        auth = await self._signup(test_client, "krelget@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        class FakeNode:
            organization_id = org_id

        mock_instance = AsyncMock()
        mock_instance.get_node.return_value = FakeNode()
        mock_instance.get_node_relations.return_value = [
            {"id": str(uuid4()), "source_name": "Python", "target_name": "Django", "relation_type": "related_to"},
        ]
        mock_service_cls.return_value = mock_instance

        resp = await test_client.get(f"/api/v1/knowledge/nodes/{uuid4()}/relations")
        assert resp.status_code == 200, f"get relations failed: {resp.text}"
        assert len(resp.json()) == 1

    @patch("app.presentation.routes.knowledge.knowledge_routes.GraphStore", autospec=True)
    async def test_get_memories(self, mock_graph_store_cls, test_client, integration_session_factory):
        mock_store = AsyncMock(spec=GraphStore)
        mock_store.get_memories = AsyncMock(return_value=[
            {"id": str(uuid4()), "key": "pref", "value": "admin", "type": "conversation"},
        ])
        mock_graph_store_cls.return_value = mock_store

        auth = await self._signup(test_client, "kmget@test.com")
        user_id = UUID(auth["user"]["id"])
        org_id = await self._create_org_with_owner(integration_session_factory, user_id)
        test_client.headers["Authorization"] = f"Bearer {auth['access_token']}"

        resp = await test_client.get(
            f"/api/v1/knowledge/memory/{org_id}/{user_id}",
        )
        assert resp.status_code == 200, f"get memories failed: {resp.text}"
        assert len(resp.json()) == 1

    async def test_knowledge_unauthorized(self, test_client):
        resp = await test_client.post(
            "/api/v1/knowledge/nodes",
            json={
                "organization_id": str(uuid4()),
                "type": "concept",
                "name": "Hack",
            },
        )
        assert resp.status_code in (401, 403)
