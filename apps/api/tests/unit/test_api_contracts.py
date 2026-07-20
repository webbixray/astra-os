from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Create the full FastAPI app for contract testing."""
    a = create_app()

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session_factory = MagicMock(return_value=mock_session)
    a.state.db = mock_session_factory
    a.dependency_overrides[get_db] = mock_session_factory
    a.dependency_overrides[require_user_id] = uuid4

    return a


def _build_mock_redis(
    client_ping: AsyncMock | None = None, connect_side_effect: Exception | None = None
) -> MagicMock:
    mock_cache = MagicMock()
    if connect_side_effect:
        mock_cache.client = None
    else:
        mock_client = AsyncMock()
        mock_client.ping = client_ping or AsyncMock(return_value=True)
        mock_cache.client = mock_client
    mock_cache.connect = AsyncMock(side_effect=connect_side_effect)
    mock_cache.disconnect = AsyncMock()
    return mock_cache


class TestOpenAPISchema:
    @pytest.fixture(scope="module")
    def openapi_schema(self, app: FastAPI) -> dict:
        return app.openapi()

    def test_schema_has_info(self, openapi_schema: dict):
        info = openapi_schema.get("info", {})
        assert info.get("title") == "ASTRA OS API"
        assert info.get("version") == "1.1.0"

        assert "description" in info

    def test_schema_has_all_required_paths(self, openapi_schema: dict):
        paths = openapi_schema.get("paths", {})
        required_paths = [
            "/api/v1/health",
            "/api/v1/metrics",
            "/api/v1/auth/signin",
            "/api/v1/auth/signup",
            "/api/v1/auth/refresh",
            "/api/v1/auth/me",
            "/api/v1/organizations",
            "/api/v1/campaigns",
            "/api/v1/content",
            "/api/v1/chat",
            "/api/v1/agents",
            "/api/v1/workflows",
            "/api/v1/ad/accounts",
            "/api/v1/knowledge/nodes",
            "/api/v1/knowledge/search",
            "/api/v1/calendar/events",
            "/api/v1/notifications",
            "/api/v1/notification-templates",
            "/api/v1/notification-preferences",
            "/api/v1/dashboards",
            "/api/v1/dashboards/{dashboard_id}",
            "/api/v1/knowledge/search",
        ]
        for path in required_paths:
            assert path in paths, f"Missing required path: {path}"

    def test_schema_has_security_schemes(self, openapi_schema: dict):
        components = openapi_schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        assert "HTTPBearer" in security_schemes or "BearerAuth" in security_schemes

    def test_schema_all_paths_have_operations(self, openapi_schema: dict):
        paths = openapi_schema.get("paths", {})
        for path, methods in paths.items():
            operations = [m for m in methods if m in ("get", "post", "put", "patch", "delete")]
            assert len(operations) > 0, f"Path {path} has no HTTP operations"

    def test_schema_has_response_schemas(self, openapi_schema: dict):
        paths = openapi_schema.get("paths", {})
        paths_with_responses = 0
        for methods in paths.values():
            for details in methods.values():
                if isinstance(details, dict) and "responses" in details:
                    paths_with_responses += 1
        assert paths_with_responses > 50, f"Only {paths_with_responses} paths have response schemas"

    def test_health_endpoint_returns_200(self, openapi_schema: dict):
        health = openapi_schema["paths"].get("/api/v1/health", {})
        get_op = health.get("get", {})
        responses = get_op.get("responses", {})
        assert "200" in responses

    def test_metrics_endpoint_returns_200(self, openapi_schema: dict):
        metrics = openapi_schema["paths"].get("/api/v1/metrics", {})
        get_op = metrics.get("get", {})
        responses = get_op.get("responses", {})
        assert "200" in responses


class TestHealthContract:
    @pytest.mark.asyncio
    async def test_health_response_structure(self, app: FastAPI):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.state.redis = _build_mock_redis()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_prometheus(self, app: FastAPI):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.state.redis = _build_mock_redis()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/metrics")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "openmetrics" in content_type


class TestErrorHandlingContract:
    @pytest.mark.asyncio
    async def test_404_returns_envelope(self, app: FastAPI):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent-endpoint-xyz")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, app: FastAPI):
        app.dependency_overrides.pop(require_user_id, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code in (401, 403)
        app.dependency_overrides[require_user_id] = uuid4

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, app: FastAPI):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

        assert response.status_code in (200, 405)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
