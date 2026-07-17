import asyncio
import logging
import os
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.domain.common import now
from app.presentation.dependencies import get_db
from app.presentation.schemas.common import HealthResponse

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/health", summary="Check application health")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}
    start = time.monotonic()

    t0 = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
        details["database_ms"] = f"{(time.monotonic() - t0) * 1000:.1f}"
    except Exception as e:
        checks["database"] = False
        details["database"] = "unavailable"
        logger.warning("Health check database failure: %s", type(e).__name__)

    redis_cache = getattr(request.app.state, "redis", None)
    if redis_cache and redis_cache.client:
        try:
            t0 = time.monotonic()
            await asyncio.wait_for(redis_cache.client.ping(), timeout=3.0)
            checks["redis"] = True
            details["redis_ms"] = f"{(time.monotonic() - t0) * 1000:.1f}"
        except Exception as e:
            checks["redis"] = False
            details["redis"] = "unavailable"
            logger.warning("Health check redis failure: %s", type(e).__name__)
    elif config.redis_url:
        checks["redis"] = False
        details["redis"] = "not_connected"
    else:
        checks["redis"] = True
        details["redis"] = "not_configured"

    if config.temporal_host:
        try:
            from temporalio.client import Client

            t0 = time.monotonic()
            client = await asyncio.wait_for(Client.connect(config.temporal_host), timeout=5.0)
            await client.service.health_check()
            await client.close()
            checks["temporal"] = True
            details["temporal_ms"] = f"{(time.monotonic() - t0) * 1000:.1f}"
        except ImportError:
            checks["temporal"] = True
            details["temporal"] = "not_configured"
        except Exception as e:
            checks["temporal"] = False
            details["temporal"] = "unavailable"
            logger.warning("Health check temporal failure: %s", type(e).__name__)
    else:
        checks["temporal"] = True
        details["temporal"] = "not_configured"

    all_ok = all(checks.values())
    elapsed = time.monotonic() - start
    return HealthResponse(
        status="ok" if all_ok else "degraded",
        version=os.getenv("APP_VERSION", "0.0.1"),
        timestamp=now(),
        checks=checks,
        details=details,
        duration_ms=f"{elapsed * 1000:.1f}",
    )


@router.get("/health/live", summary="Check liveness")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", summary="Check readiness")
async def readiness(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    status_val = "ready"
    checks: dict[str, bool] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
        status_val = "not_ready"

    redis_cache = getattr(request.app.state, "redis", None)
    if redis_cache and redis_cache.client:
        try:
            await asyncio.wait_for(redis_cache.client.ping(), timeout=2.0)
            checks["redis"] = True
        except Exception:
            checks["redis"] = False
            status_val = "not_ready"
    elif config.redis_url:
        checks["redis"] = False
        status_val = "not_ready"
    else:
        checks["redis"] = True

    return {"status": status_val, "checks": checks}


@router.get("/", summary="Get API root info")
async def root() -> dict[str, str]:
    return {
        "service": "ASTRA OS API",
        "version": os.getenv("APP_VERSION", "0.0.1"),
        "environment": config.environment,
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
    }
