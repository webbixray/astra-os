"""API versioning middleware.

Adds standard API version headers to all responses and emits deprecation
warnings for endpoints that opt in via the ``deprecated`` marker on the route.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)

# Current API version advertised in headers
_API_VERSION = "2024-12-01"
_API_DEPRECATED_HEADER = "Deprecation"
_API_SUNSET_HEADER = "Sunset"
_API_LINK_HEADER = "Link"


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Attaches API version and deprecation headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Always advertise the current API version
        response.headers["X-API-Version"] = _API_VERSION

        # If the matched route is marked deprecated, add deprecation headers
        route = request.scope.get("route")
        if route is not None and getattr(route, "deprecated", False):
            response.headers[_API_DEPRECATED_HEADER] = "true"
            response.headers[_API_SUNSET_HEADER] = "Sat, 01 Dec 2026 00:00:00 GMT"
            response.headers[_API_LINK_HEADER] = '</api/v2>; rel="successor-version"'
            logger.info(
                "Deprecated endpoint called: %s %s",
                request.method,
                request.url.path,
            )

        return response
