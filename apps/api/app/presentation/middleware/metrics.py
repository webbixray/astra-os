import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.infrastructure.metrics import (
    http_request_duration_seconds,
    http_requests_in_flight,
    http_requests_total,
)

HEALTH_PATH_RE = re.compile(r"^/api/v1/health/?")
METRICS_PATH_RE = re.compile(r"^/api/v1/metrics/?")
UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
NUMERIC_ID_RE = re.compile(r"/\d+(?=/|$)")


def _normalize_path(path: str) -> str:
    path = UUID_RE.sub("{id}", path)
    return NUMERIC_ID_RE.sub("/{id}", path)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if HEALTH_PATH_RE.match(path) or METRICS_PATH_RE.match(path):
            return await call_next(request)

        method = request.method
        normalized = _normalize_path(path)
        http_requests_in_flight.labels(method=method).inc()
        start = time.monotonic()

        response = await call_next(request)

        duration = time.monotonic() - start
        http_requests_total.labels(
            method=method, path=normalized, status=response.status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=method, path=normalized
        ).observe(duration)
        http_requests_in_flight.labels(method=method).dec()
        return response
