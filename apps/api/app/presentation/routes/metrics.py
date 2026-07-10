from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.infrastructure.metrics import (
    campaigns_created,
    users_signed_up,
    workflows_completed,
    workflows_failed,
)

router = APIRouter()


@router.get("/metrics", summary="Prometheus metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/metrics/business", summary="Business metrics")
async def business_metrics() -> dict[str, int]:
    return {
        "users_signed_up": users_signed_up._value.get(),
        "campaigns_created": campaigns_created._value.get(),
        "workflows_completed": workflows_completed._value.get(),
        "workflows_failed": workflows_failed._value.get(),
    }
