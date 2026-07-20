from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.presentation.middleware.response_envelope import EnvelopeMiddleware, _is_enveloped


class TestIsEnveloped:
    def test_enveloped_success(self) -> None:
        assert _is_enveloped({"success": True, "data": {"key": "val"}}) is True

    def test_enveloped_error(self) -> None:
        assert _is_enveloped({"success": False, "code": "err", "message": "oops"}) is True

    def test_enveloped_paginated(self) -> None:
        assert (
            _is_enveloped(
                {"success": True, "data": [], "total": 0, "page": 1, "limit": 10, "pages": 0}
            )
            is True
        )

    def test_plain_dict(self) -> None:
        assert _is_enveloped({"key": "val"}) is False

    def test_plain_list(self) -> None:
        assert _is_enveloped([1, 2, 3]) is False

    def test_plain_string(self) -> None:
        assert _is_enveloped("hello") is False


class TestEnvelopeMiddleware:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()

        @app.get("/api/v1/plain")
        async def plain() -> dict:
            return {"key": "value"}

        @app.get("/api/v1/list")
        async def list_data() -> list:
            return [1, 2, 3]

        @app.get("/api/v1/already-wrapped")
        async def wrapped() -> dict:
            return {"success": True, "data": {"id": 1}}

        @app.get("/api/v1/health")
        async def health() -> dict:
            return {"status": "ok"}

        app.add_middleware(EnvelopeMiddleware)
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_wraps_plain_dict(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/plain")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"success": True, "data": {"key": "value"}}

    async def test_wraps_plain_list(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"success": True, "data": [1, 2, 3]}

    async def test_does_not_double_wrap(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/already-wrapped")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"success": True, "data": {"id": 1}}

    async def test_skips_health_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"status": "ok"}

    async def test_passes_through_errors(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/nonexistent")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Not Found"}


class TestEnvelopeMiddlewareCustomExclude:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()

        @app.get("/custom")
        async def custom() -> dict:
            return {"key": "value"}

        app.add_middleware(EnvelopeMiddleware, exclude_prefixes=("/custom",))
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_excludes_custom_path(self, client: AsyncClient) -> None:
        resp = await client.get("/custom")
        assert resp.status_code == 200
        assert resp.json() == {"key": "value"}
