from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import ClassVar

from app.config import config

logger = logging.getLogger(__name__)


class StartupProbe:
    warnings: ClassVar[list[str]] = []
    errors: ClassVar[list[str]] = []

    @classmethod
    def run_all(cls) -> None:
        cls.warnings.clear()
        cls.errors.clear()
        cls._check_secret_key()
        cls._check_cors_origins()
        cls._check_database_url()
        cls._check_redis_url()
        cls._check_ssl_certs()
        cls._check_env_file()
        cls._check_ai_providers()
        cls._check_supabase()

        if cls.errors:
            for err in cls.errors:
                logger.critical("STARTUP BLOCKER: %s", err)
            sys.exit(1)

        for warn in cls.warnings:
            logger.warning("Startup warning: %s", warn)

        if not cls.errors and not cls.warnings:
            logger.info("All startup checks passed")

    @classmethod
    def _check_secret_key(cls) -> None:
        if not config.secret_key or len(config.secret_key) < 32:
            cls.errors.append(
                "SECRET_KEY must be at least 32 characters. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )

    @classmethod
    def _check_cors_origins(cls) -> None:
        origins = config.cors_origin_list
        if not origins or origins == ["*"]:
            if config.is_production:
                cls.errors.append("CORS_ORIGINS cannot be '*' in production. Set specific origins.")
            else:
                cls.warnings.append("CORS_ORIGINS is not configured or set to '*'")

    @classmethod
    def _check_database_url(cls) -> None:
        if not config.database_url or "astra_dev" in config.database_url:
            if config.is_production:
                cls.errors.append("DATABASE_URL contains default development credentials.")
            else:
                cls.warnings.append("DATABASE_URL uses default development credentials")

    @classmethod
    def _check_redis_url(cls) -> None:
        if not config.redis_url:
            cls.warnings.append("REDIS_URL is not set. Rate limiting and caching will be degraded.")

    @classmethod
    def _check_ssl_certs(cls) -> None:
        ssl_dir = Path(__file__).parent.parent.parent / "docker" / "prod" / "ssl"
        cert_path = ssl_dir / "cert.pem"
        key_path = ssl_dir / "key.pem"
        if cert_path.exists() or key_path.exists():
            cls.warnings.append(
                "Development SSL certificates found in docker/prod/ssl/. "
                "Replace these with production certificates."
            )

    @classmethod
    def _check_env_file(cls) -> None:
        env_file = Path(__file__).parent.parent.parent / ".env"
        if not env_file.exists():
            cls.warnings.append(
                "No .env file found. Create one based on .env.example "
                "or set all required environment variables."
            )

    @classmethod
    def _check_ai_providers(cls) -> None:
        has_any_provider = bool(
            config.openai_api_key
            or config.anthropic_api_key
            or config.gemini_api_key
            or config.nvidia_nim_base_url
        )
        if not has_any_provider:
            if config.is_production:
                cls.errors.append(
                    "No AI provider configured. Set at least one of: "
                    "OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, NVIDIA_NIM_BASE_URL"
                )
            else:
                cls.warnings.append(
                    "No AI provider configured. AI features will not work. "
                    "Set at least one: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc."
                )

    @classmethod
    def _check_supabase(cls) -> None:
        if not config.supabase_url:
            if config.is_production:
                cls.errors.append("SUPABASE_URL is required in production.")
            else:
                cls.warnings.append("SUPABASE_URL not set. Authentication may not work correctly.")
