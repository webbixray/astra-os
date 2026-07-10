import os
import secrets

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    environment: str = Field(default="development", pattern=r"^(development|staging|production)$")
    secret_key: str = Field(default="", min_length=32)
    debug: bool = False
    cors_origins: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+asyncpg://astra:astra_dev@localhost:5432/astra",
        pattern=r"^postgresql(\+asyncpg)?://",
    )
    redis_url: str = "redis://localhost:6379/0"
    temporal_host: str = "localhost:7233"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    nvidia_nim_base_url: str = ""

    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_developer_token: str = ""
    google_ads_refresh_token: str = ""

    meta_access_token: str = ""
    meta_ad_account_id: str = ""

    linkedin_access_token: str = ""
    linkedin_organization_id: str = ""

    tiktok_access_token: str = ""
    tiktok_advertiser_id: str = ""

    sentry_dsn: str = ""
    otlp_endpoint: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or v == "change_me_in_production":
            if os.environ.get("ENVIRONMENT", "").lower() == "production":
                raise ValueError(
                    "SECRET_KEY must be set to a secure random value of at least 32 characters "
                    "when running in production mode."
                )
            return secrets.token_urlsafe(48)
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        if v == "*":
            raise ValueError("CORS_ORIGINS cannot be '*' in production. Specify exact origins.")
        return v

    @model_validator(mode="after")
    def validate_production(self) -> "AppConfig":
        if os.environ.get("ENVIRONMENT", "").lower() == "production":
            required_in_prod: dict[str, str] = {
                "OPENAI_API_KEY": self.openai_api_key,
                "SUPABASE_URL": self.supabase_url,
                "SUPABASE_ANON_KEY": self.supabase_anon_key,
            }
            missing = [k for k, v in required_in_prod.items() if not v]
            if missing:
                raise ValueError(
                    f"Production environment requires: {', '.join(missing)}"
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def csp_policy(self) -> str | None:
        if self.is_production:
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self' https://*.sentry.io; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "object-src 'none'"
            )
        return None


config = AppConfig()
