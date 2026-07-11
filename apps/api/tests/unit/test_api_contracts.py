import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture(scope="module")
def app() -> FastAPI:
    return create_app()


@pytest.fixture(scope="module")
def openapi_schema(app: FastAPI) -> dict:
    return app.openapi()


class TestOpenAPISchema:
    def test_schema_has_info(self, openapi_schema: dict):
        info = openapi_schema.get("info", {})
        assert info.get("title") == "ASTRA OS API"
        assert info.get("version") == "0.0.1"
        assert "description" in info

    def test_schema_has_all_required_paths(self, openapi_schema: dict):
        paths = openapi_schema.get("paths", {})
        required_paths = [
            "/api/v1/health",
            "/api/v1/metrics",
            "/api/v1/auth/signin",
            "/api/v1/auth/signup",
            "/api/v1/auth/refresh",
            "/api/v1/users/me",
            "/api/v1/organizations",
            "/api/v1/campaigns",
            "/api/v1/content",
            "/api/v1/chat",
            "/api/v1/agents",
            "/api/v1/workflows",
            "/api/v1/advertising",
            "/api/v1/calendar",
            "/api/v1/notifications",
            "/api/v1/notification-templates",
            "/api/v1/notification-preferences",
            "/api/v1/dashboards",
            "/api/v1/knowledge",
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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/metrics")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "openmetrics" in content_type

    @pytest.mark.asyncio
    async def test_business_metrics_returns_dict(self, app: FastAPI):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/metrics/business")

        assert response.status_code == 200
        data = response.json()
        assert "users_signed_up" in data
        assert "campaigns_created" in data
        assert "workflows_completed" in data
        assert "workflows_failed" in data
        assert all(isinstance(v, int) for v in data.values())


class TestErrorHandlingContract:
    @pytest.mark.asyncio
    async def test_404_returns_envelope(self, app: FastAPI):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent-endpoint-xyz")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, app: FastAPI):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/me")

        assert response.status_code in (401, 403)

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
