from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt
from app.main import create_app
from app.presentation.middleware.auth import require_user_id
from app.presentation.routes.ai.prompt_routes import get_manage_use_case


def _mock_prompt(**kwargs) -> MagicMock:
    p = MagicMock(spec=SystemPrompt)
    p.id = kwargs.get("id", uuid4())
    p.org_id = kwargs.get("org_id")
    p.name = kwargs.get("name", "test_prompt")
    p.description = kwargs.get("description", "")
    p.category = kwargs.get("category", PromptCategory.SYSTEM)
    p.content = kwargs.get("content", "Test content")
    p.variables = kwargs.get("variables", [])
    p.version = kwargs.get("version", 1)
    p.status = kwargs.get("status", PromptStatus.ACTIVE)
    p.is_builtin = kwargs.get("is_builtin", False)
    p.created_by = kwargs.get("created_by")
    p.created_at = kwargs.get("created_at", __import__("datetime").datetime.now())
    p.updated_at = kwargs.get("updated_at", __import__("datetime").datetime.now())
    p.bump_version = MagicMock()
    return p


_PASSWORD_HASH = ""


def _setup_csrf(client):
    import hashlib
    import hmac
    import secrets
    import time

    from app.config import config
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
    return {"X-CSRF-Token": csrf_token}


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

    a.dependency_overrides[require_user_id] = uuid4

    yield a
    a.dependency_overrides.clear()


@pytest.fixture
async def test_client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_use_case() -> MagicMock:
    uc = MagicMock()
    uc.list_prompts = AsyncMock(return_value=[])
    uc.get_prompt = AsyncMock()
    uc.create_prompt = AsyncMock()
    uc.update_prompt = AsyncMock()
    uc.delete_prompt = AsyncMock()
    return uc


class TestPromptRoutes:
    @pytest.mark.asyncio
    async def test_list_prompts_empty(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case
        response = await test_client.get("/api/v1/prompts")
        assert response.status_code == 200
        assert response.json() == {"success": True, "data": []}

    @pytest.mark.asyncio
    async def test_list_prompts_with_category(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        prompts = [
            _mock_prompt(name="p1", category=PromptCategory.CONTENT),
            _mock_prompt(name="p2", category=PromptCategory.CONTENT),
        ]
        mock_use_case.list_prompts = AsyncMock(return_value=prompts)
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        response = await test_client.get("/api/v1/prompts?category=content")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["category"] == "content"

    @pytest.mark.asyncio
    async def test_list_prompts_with_org(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        org_id = uuid4()
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        await test_client.get(f"/api/v1/prompts?org_id={org_id}")
        mock_use_case.list_prompts.assert_awaited_once()
        call_args = mock_use_case.list_prompts.await_args
        assert call_args is not None
        assert str(call_args.kwargs.get("org_id", "")) == str(org_id)

    @pytest.mark.asyncio
    async def test_get_prompt_found(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        prompt_id = uuid4()
        prompt = _mock_prompt(id=prompt_id, name="found")
        mock_use_case.get_prompt = AsyncMock(return_value=prompt)
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/prompts/{prompt_id}")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "found"

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        mock_use_case.get_prompt = AsyncMock(return_value=None)
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/prompts/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_prompt(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        prompt_id = uuid4()
        prompt = _mock_prompt(id=prompt_id, name="new_prompt", content="Hello")
        mock_use_case.create_prompt = AsyncMock(return_value=prompt)
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.post(
            "/api/v1/prompts",
            json={"name": "new_prompt", "content": "Hello"},
            headers=csrf,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "new_prompt"
        assert data["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_create_prompt_invalid_category(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.post(
            "/api/v1/prompts",
            json={"name": "bad", "content": "x", "category": "invalid"},
            headers=csrf,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_prompt(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        prompt_id = uuid4()
        prompt = _mock_prompt(id=prompt_id, name="updated", content="new content")
        mock_use_case.update_prompt = AsyncMock(return_value=prompt)
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.patch(
            f"/api/v1/prompts/{prompt_id}",
            json={"content": "new content", "description": "updated desc"},
            headers=csrf,
        )
        assert response.status_code == 200
        assert response.json()["data"]["content"] == "new content"

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        mock_use_case.update_prompt = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Prompt not found")
        )
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.patch(
            f"/api/v1/prompts/{uuid4()}",
            json={"content": "updated"},
            headers=csrf,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_prompt_invalid_status(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.patch(
            f"/api/v1/prompts/{uuid4()}",
            json={"status": "nonexistent"},
            headers=csrf,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_prompt(
        self, app: FastAPI, test_client: AsyncClient, mock_use_case: MagicMock
    ):
        mock_use_case.delete_prompt = AsyncMock()
        app.dependency_overrides[get_manage_use_case] = lambda: mock_use_case

        csrf = _setup_csrf(test_client)
        response = await test_client.delete(f"/api/v1/prompts/{uuid4()}", headers=csrf)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_list_builtins(
        self, app: FastAPI, test_client: AsyncClient
    ):
        response = await test_client.get("/api/v1/prompts/builtins")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] in (
            "system_chat", "content_writer", "content_rewriter",
            "agent_ceo", "agent_campaign_director", "agent_content_director",
            "agent_analytics_director", "agent_workflow_director", "slash_commands",
        )
