from __future__ import annotations

import logging

from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.infrastructure.metrics import (
    campaigns_created,
    users_signed_up,
    workflows_completed,
    workflows_failed,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics", summary="Prometheus metrics")
async def metrics() -> Response:
    try:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
    except Exception:
        logger.exception("Failed to generate Prometheus metrics")
        return Response(content="# Error generating metrics\n", media_type="text/plain", status_code=500)


def _safe_get(counter) -> int:
    try:
        return int(counter._value.get())
    except Exception:
        return 0


@router.get("/metrics/business", summary="Business metrics")
async def business_metrics() -> dict[str, int]:
    return {
        "users_signed_up": _safe_get(users_signed_up),
        "campaigns_created": _safe_get(campaigns_created),
        "workflows_completed": _safe_get(workflows_completed),
        "workflows_failed": _safe_get(workflows_failed),
    }
