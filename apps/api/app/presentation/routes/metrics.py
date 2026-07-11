from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.infrastructure.metrics import (
    campaigns_created,
    users_signed_up,
    workflows_completed,
    workflows_failed,
)
from app.presentation.middleware.auth import require_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


def _safe_get(counter) -> int:
    try:
        return int(counter._value.get())
    except Exception:
        return 0


@router.get("/metrics", summary="Prometheus metrics (public)")
async def metrics() -> Response:
    """Public Prometheus metrics endpoint - no authentication required."""
    try:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
    except Exception:
        logger.exception("Failed to generate Prometheus metrics")
        return Response(
            content="# Error generating metrics\n", media_type="text/plain", status_code=500
        )


@router.get("/metrics/business", summary="Business metrics (authenticated)")
async def business_metrics(user_id: UUID = Depends(require_user_id)) -> dict[str, int]:
    return {
        "users_signed_up": _safe_get(users_signed_up),
        "campaigns_created": _safe_get(campaigns_created),
        "workflows_completed": _safe_get(workflows_completed),
        "workflows_failed": _safe_get(workflows_failed),
    }
