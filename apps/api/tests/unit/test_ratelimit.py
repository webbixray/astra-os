from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.presentation.middleware.ratelimit import RateLimitMiddleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/test")
    async def normal_route() -> dict:
        return {"ok": True}

    @app.get("/api/v1/health")
    async def health_route() -> dict:
        return {"status": "ok"}

    @app.post("/api/v1/auth/signin")
    async def signin_route() -> dict:
        return {"success": True}

    return app


class TestRateLimitMiddleware:
    async def test_allows_normal_request(self):
        app = FastAPI()

        @app.get("/test")
        async def route() -> dict:
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, requests_per_minute=120, whitelist_paths=[])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
        assert response.status_code == 200

    async def test_whitelist_bypasses_limit(self):
        app = FastAPI()

        @app.get("/api/v1/health")
        async def health() -> dict:
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, requests_per_minute=1, whitelist_paths=["/api/v1/health"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.get("/api/v1/health")
            resp2 = await client.get("/api/v1/health")
        assert resp1.status_code == 200
        assert resp2.status_code == 200

    async def test_returns_429_when_exceeded(self):
        app = FastAPI()

        @app.get("/api/v1/test")
        async def route() -> dict:
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, requests_per_minute=1, whitelist_paths=[])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.get("/api/v1/test")
            resp2 = await client.get("/api/v1/test")
        assert resp1.status_code == 200
        assert resp2.status_code == 429
        data = resp2.json()
        assert data["code"] == "rate_limit_exceeded"

    async def test_auth_path_has_stricter_limit(self):
        app = FastAPI()

        @app.post("/api/v1/auth/signin")
        async def signin() -> dict:
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, auth_requests_per_minute=1, requests_per_minute=120, whitelist_paths=[])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.post("/api/v1/auth/signin")
            resp2 = await client.post("/api/v1/auth/signin")
        assert resp1.status_code == 200
        assert resp2.status_code == 429

    async def test_local_window_sliding(self):
        app = FastAPI()

        @app.get("/api/v1/test")
        async def route() -> dict:
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, requests_per_minute=3, whitelist_paths=[])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                resp = await client.get("/api/v1/test")
                assert resp.status_code == 200
            resp = await client.get("/api/v1/test")
            assert resp.status_code == 429

    async def test_uses_redis_when_available(self):
        app = FastAPI()
        app.state = MagicMock()

        @app.get("/api/v1/test")
        async def route() -> dict:
            return {"ok": True}

        redis_mock = AsyncMock()
        redis_mock.client.get = AsyncMock(return_value=0)
        redis_mock.client.incr = AsyncMock(return_value=1)
        redis_mock.client.expire = AsyncMock()

        app.add_middleware(RateLimitMiddleware, requests_per_minute=120, whitelist_paths=[], redis_cache=redis_mock)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/test")
        assert response.status_code == 200
