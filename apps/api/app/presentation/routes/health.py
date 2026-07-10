import asyncio
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
        details["database"] = str(e)

    redis_cache = getattr(request.app.state, "redis", None)
    if redis_cache and redis_cache.client:
        try:
            t0 = time.monotonic()
            await asyncio.wait_for(redis_cache.client.ping(), timeout=3.0)
            checks["redis"] = True
            details["redis_ms"] = f"{(time.monotonic() - t0) * 1000:.1f}"
        except Exception as e:
            checks["redis"] = False
            details["redis"] = str(e)
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
            client = await asyncio.wait_for(
                Client.connect(config.temporal_host), timeout=5.0
            )
            await client.service.health_check()
            await client.close()
            checks["temporal"] = True
            details["temporal_ms"] = f"{(time.monotonic() - t0) * 1000:.1f}"
        except ImportError:
            checks["temporal"] = True
            details["temporal"] = "not_configured"
        except Exception as e:
            checks["temporal"] = False
            details["temporal"] = str(e)
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
async def readiness(request: Request) -> dict[str, object]:
    status = "ready"
    checks: dict[str, bool] = {}

    if getattr(request.app.state, "db", None):
        checks["database"] = True
    else:
        checks["database"] = False
        status = "not_ready"

    redis = getattr(request.app.state, "redis", None)
    if redis and redis.client:
        checks["redis"] = True
    else:
        checks["redis"] = False
        status = "not_ready"

    return {"status": status, "checks": checks}


@router.get("/", summary="Get API root info")
async def root() -> dict[str, str]:
    return {
        "service": "ASTRA OS API",
        "version": os.getenv("APP_VERSION", "0.0.1"),
        "environment": config.environment,
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
    }
