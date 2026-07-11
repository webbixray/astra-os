"""Audit middleware for logging mutating requests."""

import json
import logging
import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.audit.audit_service import AuditService
from app.presentation.dependencies import get_db

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)

# Methods that mutate state
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to exclude from audit logging
EXCLUDED_PATHS = {
    "/api/v1/health",
    "/api/v1/metrics",
    "/api/v1/auth/signin",
    "/api/v1/auth/signup",
    "/api/v1/auth/refresh",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Log mutating requests to audit trail."""

    async def dispatch(self, request: Request, call_next):
        # Skip non-mutating methods
        if request.method not in MUTATING_METHODS:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in EXCLUDED_PATHS):
            return await call_next(request)

        # Capture request body for audit
        request_body = None
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode("utf-8"))
            except Exception:
                request_body = "<unable to parse>"

        # Get user and tenant from request state
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Capture response body for audit (only for errors or important actions)
        response_body = None
        if response.status_code >= 400:
            try:
                response_body_raw = b""
                async for chunk in response.body_iterator:
                    response_body_raw += chunk
                if response_body_raw:
                    response_body = json.loads(response_body_raw.decode("utf-8"))
            except Exception:
                response_body = "<unable to parse>"

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log to audit trail (async, fire-and-forget)
        try:
            await self._log_audit(
                request=request,
                user_id=user_id,
                tenant_id=tenant_id,
                request_body=request_body,
                response_status=response.status_code,
                response_body=response_body,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error("Failed to write audit log: %s", e)

        return response

    async def _log_audit(
        self,
        request: Request,
        user_id: "UUID | None",
        tenant_id: "UUID | None",
        request_body: dict | None,
        response_status: int,
        response_body: dict | None,
        duration_ms: int,
    ) -> None:
        """Write audit entry to database."""
        # Get DB session from app state
        from app.presentation.dependencies import get_db_session_factory

        session_factory = get_db_session_factory(request.app)
        if not session_factory:
            return

        async with session_factory() as session:
            audit_service = AuditService(session)

            # Extract resource info from path
            resource_type, resource_id = self._extract_resource_info(request.url.path)

            action = f"{request.method} {resource_type}" if resource_type else request.method

            await audit_service.log(
                action=action,
                resource_type=resource_type or "unknown",
                resource_id=resource_id or "unknown",
                actor_id=user_id,
                organization_id=tenant_id,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "request_body": request_body,
                    "response_status": response_status,
                    "response_body": response_body,
                    "duration_ms": duration_ms,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                },
            )

    def _extract_resource_info(self, path: str) -> tuple[str | None, str | None]:
        """Extract resource type and ID from path like /api/v1/campaigns/{id}."""
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            resource_type = parts[2].rstrip("s")  # campaigns -> campaign
            # Check if next part is a UUID
            if len(parts) > 3:
                resource_id = parts[3]
                return resource_type, resource_id
            return resource_type, None
        return None, None