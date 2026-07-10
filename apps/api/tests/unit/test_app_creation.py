from fastapi import FastAPI

from app.main import create_app


class TestAppCreation:
    def test_create_app_returns_fastapi(self):
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_create_app_has_route_count(self):
        app = create_app()
        included = [r for r in app.routes if type(r).__name__ == "_IncludedRouter"]
        assert len(included) >= 20

    def test_create_app_has_middleware(self):
        app = create_app()
        assert len(app.user_middleware) > 0

    def test_create_app_title(self):
        app = create_app()
        assert app.title == "ASTRA OS API"

    def test_create_app_version(self):
        app = create_app()
        assert app.version == "0.0.1"

    def test_openapi_generates(self):
        app = create_app()
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert len(paths) > 100
        assert "/api/v1/health" in paths
        assert "/api/v1/auth/signin" in paths
        assert "/api/v1/metrics" in paths
