from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.startup import StartupProbe


@pytest.fixture(autouse=True)
def reset_probe():
    StartupProbe.warnings.clear()
    StartupProbe.errors.clear()


def _mock_config(**kwargs):
    mock = MagicMock()
    for k, v in kwargs.items():
        setattr(mock, k, v)
    return mock


class TestStartupProbe:
    def test_clears_on_run(self):
        StartupProbe.warnings.append("leftover")
        StartupProbe.run_all()
        assert "leftover" not in StartupProbe.warnings

    def test_secret_key_missing(self):
        with patch("app.infrastructure.startup.config.secret_key", ""):
            StartupProbe._check_secret_key()
            assert any("SECRET_KEY" in e for e in StartupProbe.errors)

    def test_secret_key_short(self):
        with patch("app.infrastructure.startup.config.secret_key", "short"):
            StartupProbe._check_secret_key()
            assert any("SECRET_KEY" in e for e in StartupProbe.errors)

    def test_secret_key_ok(self):
        with patch("app.infrastructure.startup.config.secret_key", "a" * 32):
            StartupProbe._check_secret_key()
            assert not StartupProbe.errors

    def test_cors_wildcard_production(self):
        mock = MagicMock()
        mock.cors_origin_list = ["*"]
        mock.is_production = True
        mock.secret_key = "x" * 32
        mock.database_url = ""
        mock.redis_url = ""
        with patch("app.infrastructure.startup.config", mock):
            StartupProbe._check_cors_origins()
            assert any("CORS_ORIGINS" in e for e in StartupProbe.errors)

    def test_cors_wildcard_dev(self):
        mock = MagicMock()
        mock.cors_origin_list = ["*"]
        mock.is_production = False
        mock.secret_key = "x" * 32
        mock.database_url = ""
        mock.redis_url = ""
        with patch("app.infrastructure.startup.config", mock):
            StartupProbe._check_cors_origins()
            assert any("CORS_ORIGINS" in w for w in StartupProbe.warnings)

    def test_cors_configured(self):
        mock = MagicMock()
        mock.cors_origin_list = ["https://example.com"]
        mock.is_production = False
        mock.secret_key = "x" * 32
        mock.database_url = ""
        mock.redis_url = ""
        with patch("app.infrastructure.startup.config", mock):
            StartupProbe._check_cors_origins()
            assert not StartupProbe.errors
            assert not StartupProbe.warnings

    def test_database_dev_creds_production(self):
        mock = MagicMock()
        mock.cors_origin_list = ["*"]
        mock.is_production = True
        mock.secret_key = "x" * 32
        mock.database_url = "postgresql://astra_dev:dev@localhost:5432/astra"
        mock.redis_url = ""
        with patch("app.infrastructure.startup.config", mock):
            StartupProbe._check_database_url()
            assert any("DATABASE_URL" in e for e in StartupProbe.errors)

    def test_database_dev_creds_dev(self):
        mock = MagicMock()
        mock.cors_origin_list = ["*"]
        mock.is_production = False
        mock.secret_key = "x" * 32
        mock.database_url = "postgresql://astra_dev:dev@localhost:5432/astra"
        mock.redis_url = ""
        with patch("app.infrastructure.startup.config", mock):
            StartupProbe._check_database_url()
            assert any("DATABASE_URL" in w for w in StartupProbe.warnings)

    def test_database_url_ok(self):
        with patch(
            "app.infrastructure.startup.config.database_url",
            "postgresql://prod:pw@db.internal/prod",
        ):
            StartupProbe._check_database_url()
            assert not StartupProbe.errors
            assert not StartupProbe.warnings

    def test_redis_not_set(self):
        with patch("app.infrastructure.startup.config.redis_url", ""):
            StartupProbe._check_redis_url()
            assert any("REDIS_URL" in w for w in StartupProbe.warnings)

    def test_redis_set(self):
        with patch("app.infrastructure.startup.config.redis_url", "redis://localhost:6379"):
            StartupProbe._check_redis_url()
            assert not StartupProbe.warnings

    def test_env_file_missing(self):
        with patch("app.infrastructure.startup.Path.exists", return_value=False):
            StartupProbe._check_env_file()
            assert any(".env" in w for w in StartupProbe.warnings)

    def test_env_file_present(self):
        with patch("app.infrastructure.startup.Path.exists", return_value=True):
            StartupProbe._check_env_file()
            assert not StartupProbe.warnings

    def test_run_all_exits_on_errors(self):
        with (
            patch("app.infrastructure.startup.config.secret_key", ""),
            pytest.raises(SystemExit),
        ):
            StartupProbe.run_all()
