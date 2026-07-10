from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.dependencies import get_db
from app.presentation.routes.health import router as health_router


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(health_router, prefix="/api/v1")
    return app


def _build_mock_redis(client_ping: AsyncMock | None = None, connect_side_effect: Exception | None = None) -> MagicMock:
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


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_all_up(self, app: FastAPI):
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
        assert data["status"] == "ok"
        assert data["checks"]["database"] is True
        assert data["checks"]["redis"] is True
        assert data["version"] == "0.0.1"

    @pytest.mark.asyncio
    async def test_health_db_down(self, app: FastAPI):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

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
        assert data["status"] == "degraded"
        assert data["checks"]["database"] is False
        assert data["checks"]["redis"] is True

    @pytest.mark.asyncio
    async def test_health_redis_down(self, app: FastAPI):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.state.redis = _build_mock_redis(connect_side_effect=Exception("Redis unreachable"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] is True
        assert data["checks"]["redis"] is False

    @pytest.mark.asyncio
    async def test_health_all_down(self, app: FastAPI):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.state.redis = _build_mock_redis(connect_side_effect=Exception("Redis unreachable"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] is False
        assert data["checks"]["redis"] is False
