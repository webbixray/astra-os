import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.infrastructure.metrics import (
    campaigns_created,
    users_signed_up,
    workflows_completed,
    workflows_failed,
)
from app.presentation.middleware.metrics import MetricsMiddleware
from app.presentation.routes.metrics import router as metrics_router


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(metrics_router, prefix="/api/v1")

    @app.get("/api/v1/test")
    async def test_route() -> dict:
        return {"ok": True}

    @app.get("/api/v1/health/ping")
    async def health_route() -> dict:
        return {"status": "ok"}

    app.add_middleware(MetricsMiddleware)
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestMetricsEndpoint:
    async def test_metrics_prometheus_format(self, client):
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        body = response.text
        assert "astra_http_requests_total" in body

    async def test_metrics_business_endpoint(self, client):
        response = await client.get("/api/v1/metrics/business")
        assert response.status_code == 200
        data = response.json()
        assert "users_signed_up" in data
        assert "campaigns_created" in data
        assert "workflows_completed" in data
        assert "workflows_failed" in data

    async def test_business_metrics_reflect_inc(self, client):
        before = users_signed_up._value.get()
        users_signed_up.inc()
        campaigns_created.inc()
        workflows_completed.inc()
        workflows_failed.inc()

        response = await client.get("/api/v1/metrics/business")
        data = response.json()
        assert data["users_signed_up"] == before + 1
        assert data["campaigns_created"] >= 1
        assert data["workflows_completed"] >= 1
        assert data["workflows_failed"] >= 1


class TestMetricsMiddleware:
    async def test_returns_response(self, client):
        response = await client.get("/api/v1/test")
        assert response.status_code == 200

    async def test_skips_health(self, client):
        response = await client.get("/api/v1/health/ping")
        assert response.status_code == 200

    async def test_skips_metrics(self, client):
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
