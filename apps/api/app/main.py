import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import config
from app.domain.events.event_bus import EventBus
from app.infrastructure.cache.redis import RedisCache, RedisConfig
from app.infrastructure.db.config import DatabaseConfig
from app.infrastructure.db.session import create_session_factory
from app.infrastructure.events import (  # noqa: F401 - registers event handlers
    on_ad_account_connected,
    on_ai_content_generated,
    on_approval_requested,
    on_billing_plan_changed,
    on_campaign_activated,
    on_campaign_completed,
    on_campaign_created,
    on_content_published,
    on_email_bounced,
    on_organization_created,
    on_user_signed_in,
    on_user_signed_up,
    on_workflow_completed,
    on_workflow_failed,
)
from app.infrastructure.logging import configure_logging
from app.infrastructure.startup import StartupProbe
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middleware.api_version import APIVersionMiddleware
from app.presentation.middleware.auth import AuthMiddleware
from app.presentation.middleware.csrf import CSRFMiddleware
from app.presentation.middleware.logging import LoggingMiddleware
from app.presentation.middleware.metrics import MetricsMiddleware
from app.presentation.middleware.ratelimit import RateLimitMiddleware
from app.presentation.middleware.response_envelope import EnvelopeMiddleware
from app.presentation.middleware.security_headers import SecurityHeadersMiddleware
from app.presentation.routes import auth, health, metrics, organizations, users
from app.presentation.routes.advertising import advertising_routes
from app.presentation.routes.agents import agent_routes
from app.presentation.routes.ai import chat_routes, prompt_routes
from app.presentation.routes.ai.websocket_chat import router as ws_chat_router
from app.presentation.routes.analytics import analytics_routes
from app.presentation.routes.calendar import calendar_routes
from app.presentation.routes.campaigns import campaign_routes
from app.presentation.routes.campaigns.automation_routes import router as automation_router
from app.presentation.routes.content import content_routes, gen_routes
from app.presentation.routes.content.publishing import publishing_routes
from app.presentation.routes.dashboards.dashboard_routes import router as dashboard_router
from app.presentation.routes.email import email_routes
from app.presentation.routes.knowledge import knowledge_routes
from app.presentation.routes.monitoring.monitor_routes import router as monitor_router
from app.presentation.routes.notifications.notification_hub_routes import (
    router as notification_hub_router,
)
from app.presentation.routes.organizations_v2 import router as org_v2_router
from app.presentation.routes.reports import report_routes
from app.presentation.routes.reports.report_routes_v2 import router as report_v2_router
from app.presentation.routes.team import router as team_router
from app.presentation.routes.workflows import workflow_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting ASTRA OS API (env=%s)", config.environment)
    StartupProbe.run_all()

    db_config = DatabaseConfig()
    engine, session_factory = create_session_factory(db_config.url)
    await _verify_db_connection(engine)
    app.state.db = session_factory
    app.state.db_engine = engine

    redis_config = RedisConfig()
    redis_cache = RedisCache(redis_config)
    if config.redis_url:
        await _retry_connect_redis(redis_cache)
    app.state.redis = redis_cache

    if config.redis_url:
        try:
            await EventBus.enable_redis(config.redis_url)
        except Exception:
            logger.warning("EventBus Redis Pub/Sub initialization failed, using in-memory mode")

    if config.redis_url:
        try:
            from app.application.use_cases.notifications.notification_hub_service import (
                NotificationHubService,
            )
            await NotificationHubService.start_redis_listener()
        except Exception:
            logger.warning("Notification Redis listener startup failed", exc_info=True)

    logger.info("ASTRA OS API ready")

    try:
        yield
    finally:
        logger.info("Shutting down ASTRA OS API...")
        try:
            from app.application.use_cases.notifications.notification_hub_service import (
                NotificationHubService,
            )
            await NotificationHubService.stop_redis_listener()
        except Exception:
            logger.debug("Failed to stop notification Redis listener", exc_info=True)
        await EventBus.disable_redis()

        if app.state.redis:
            await app.state.redis.disconnect()
            logger.info("Redis disconnected")

        if app.state.db_engine:
            await app.state.db_engine.dispose()
            logger.info("Database connections closed")

        logger.info("ASTRA OS API shutdown complete")


async def _retry_connect_redis(redis_cache: RedisCache, retries: int = 5, delay: float = 2.0) -> None:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            await redis_cache.connect()
        except Exception as e:
            last_exc = e
            if attempt < retries - 1:
                logger.warning("Redis connection failed (attempt %d/%d): %s", attempt + 1, retries, e)
                await asyncio.sleep(delay * (attempt + 1))
        else:
            logger.info("Redis connected (attempt %d/%d)", attempt + 1, retries)
            return
    logger.error("Redis connection failed after %d attempts", retries)
    raise last_exc or RuntimeError("Redis connection failed") from None


async def _verify_db_connection(engine: AsyncEngine, retries: int = 5, delay: float = 2.0) -> None:
    from sqlalchemy import text

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            last_exc = e
            if attempt < retries - 1:
                logger.warning("Database connection failed (attempt %d/%d): %s", attempt + 1, retries, e)
                await asyncio.sleep(delay * (attempt + 1))
        else:
            logger.info("Database connected (attempt %d/%d)", attempt + 1, retries)
            return
    logger.error("Database connection failed after %d attempts", retries)
    raise last_exc or RuntimeError("Database connection failed") from None


def _init_sentry() -> None:
    if not config.sentry_dsn:
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.environment,
        traces_sample_rate=0.2 if config.is_production else 0.0,
        profiles_sample_rate=0.1 if config.is_production else 0.0,
    )


def _init_opentelemetry(app: FastAPI) -> None:
    if not config.otlp_endpoint:
        return
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {"service.name": "astra-api", "deployment.environment": config.environment}
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{config.otlp_endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


def create_app() -> FastAPI:
    _init_sentry()

    app = FastAPI(
        title="ASTRA OS API",
        version="0.0.1",
        description="AI-Native Marketing & Business Growth Operating System",
        lifespan=lifespan,
        root_path="",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    cors_origins = config.cors_origin_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Set-Cookie"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=120,
        whitelist_paths=[
            "/api/v1/health",
            "/api/v1/metrics",
        ],
    )
    app.add_middleware(EnvelopeMiddleware)
    app.add_middleware(APIVersionMiddleware)

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
    app.include_router(campaign_routes.router, prefix="/api/v1/campaigns", tags=["campaigns"])
    app.include_router(content_routes.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(chat_routes.router, prefix="/api/v1", tags=["ai"])
    app.include_router(agent_routes.router, prefix="/api/v1", tags=["agents"])
    app.include_router(workflow_routes.router, prefix="/api/v1/workflows", tags=["workflows"])
    app.include_router(analytics_routes.router, prefix="/api/v1", tags=["analytics"])
    app.include_router(knowledge_routes.router, prefix="/api/v1", tags=["knowledge"])
    app.include_router(advertising_routes.router, prefix="/api/v1", tags=["advertising"])
    app.include_router(calendar_routes.router, prefix="/api/v1", tags=["calendar"])
    app.include_router(team_router, prefix="/api/v1", tags=["teams"])
    app.include_router(gen_routes.router, prefix="/api/v1", tags=["ai-content"])
    app.include_router(publishing_routes.router, prefix="/api/v1", tags=["publishing"])
    app.include_router(email_routes.router, prefix="/api/v1", tags=["email"])
    app.include_router(report_routes.router, prefix="/api/v1", tags=["reports"])
    app.include_router(notification_hub_router, prefix="/api/v1", tags=["notifications"])
    app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboards"])
    app.include_router(org_v2_router, prefix="/api/v1", tags=["organizations"])
    app.include_router(report_v2_router, prefix="/api/v1", tags=["reports"])
    app.include_router(automation_router, prefix="/api/v1", tags=["automation"])
    app.include_router(monitor_router, prefix="/api/v1", tags=["monitoring"])
    app.include_router(prompt_routes.router, prefix="/api/v1", tags=["prompts"])
    app.include_router(ws_chat_router, tags=["websocket"])

    register_error_handlers(app)
    _init_opentelemetry(app)
    return app


app = create_app()
