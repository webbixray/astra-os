from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.presentation.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/test")
    async def test_route() -> dict:
        return {"ok": True}

    app.add_middleware(SecurityHeadersMiddleware)
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestSecurityHeadersMiddleware:
    async def test_sets_security_headers(self, client):
        response = await client.get("/test")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-xss-protection") == "0"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera" in response.headers.get("permissions-policy", "")
        assert "max-age=31536000" in response.headers.get("strict-transport-security", "")

    async def test_sets_csp_in_production(self, client):
        mock = MagicMock()
        mock.csp_policy = "default-src 'self'"
        with patch("app.presentation.middleware.security_headers.config", mock):
            response = await client.get("/test")
            assert response.headers.get("content-security-policy") == "default-src 'self'"

    async def test_skips_csp_when_none(self, client):
        mock = MagicMock()
        mock.csp_policy = None
        with patch("app.presentation.middleware.security_headers.config", mock):
            response = await client.get("/test")
            assert "content-security-policy" not in response.headers
