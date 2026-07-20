from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestConfigValidation:
    def test_secret_key_auto_generates_in_dev(self):
        from app.config import AppConfig
        config = AppConfig(environment="development", secret_key="")
        assert len(config.secret_key) >= 32

    def test_cors_origins_parse(self):
        from app.config import AppConfig
        config = AppConfig(cors_origins="http://localhost:3000,https://app.astra.com")
        assert config.cors_origin_list == ["http://localhost:3000", "https://app.astra.com"]

    def test_cors_origins_strip_spaces(self):
        from app.config import AppConfig
        config = AppConfig(cors_origins=" http://localhost:3000 , https://app.astra.com ")
        assert config.cors_origin_list == ["http://localhost:3000", "https://app.astra.com"]

    def test_cors_origin_rejects_wildcard(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setenv("ENVIRONMENT", "development")
            from app.config import AppConfig
            with pytest.raises(ValidationError):
                AppConfig(cors_origins="*")

    def test_is_production(self):
        from app.config import AppConfig
        dev = AppConfig(environment="development")
        prod = AppConfig(environment="production")
        assert not dev.is_production
        assert prod.is_production

    def test_database_url_pattern(self):
        from app.config import AppConfig
        config = AppConfig(database_url="postgresql+asyncpg://user:pass@host:5432/db")
        assert config.database_url.startswith("postgresql+asyncpg://")

    def test_production_validates_required_keys(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setenv("ENVIRONMENT", "production")
            m.setenv("SECRET_KEY", "a" * 32)
            from app.config import AppConfig
            with pytest.raises(ValidationError, match="Production environment requires"):
                AppConfig()

    def test_production_allows_with_keys(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setenv("ENVIRONMENT", "production")
            m.setenv("SECRET_KEY", "a" * 32)
            m.setenv("OPENAI_API_KEY", "sk-test")
            m.setenv("SUPABASE_URL", "https://test.supabase.co")
            m.setenv("SUPABASE_ANON_KEY", "test-anon-key")
            from app.config import AppConfig
            cfg = AppConfig()
            assert cfg.openai_api_key == "sk-test"
            assert cfg.supabase_url == "https://test.supabase.co"
            assert cfg.supabase_anon_key == "test-anon-key"
