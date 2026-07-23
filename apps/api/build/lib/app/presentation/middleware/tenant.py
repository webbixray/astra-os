"""Tenant resolution middleware.

Extracts tenant ID from X-Tenant-ID header or subdomain and attaches to request state.
"""

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class TenantResolutionMiddleware(BaseHTTPMiddleware):
    """Resolve tenant from header or subdomain."""

    def __init__(self, app, tenant_subdomain_enabled: bool = False, root_domain: str | None = None):
        super().__init__(app)
        self.tenant_subdomain_enabled = tenant_subdomain_enabled
        self.root_domain = root_domain

    async def dispatch(self, request: Request, call_next):
        tenant_id = None

        # 1. Check X-Tenant-ID header (explicit tenant selection)
        header_tenant = request.headers.get("X-Tenant-ID")
        if header_tenant:
            tenant_id = header_tenant

        # 2. Check subdomain (e.g., tenant1.astra.dev)
        elif self.tenant_subdomain_enabled and self.root_domain and request.client:
            host = request.headers.get("host", "").split(":")[0]
            if host.endswith(f".{self.root_domain}"):
                subdomain = host[: -len(self.root_domain) - 1]
                if subdomain and subdomain not in {"www", "api", "app", "admin"}:
                    tenant_id = subdomain

        # 3. Check for tenant in path (e.g., /t/{tenant_id}/...)
        if not tenant_id:
            path_match = re.match(r"^/t/([^/]+)", request.url.path)
            if path_match:
                tenant_id = path_match.group(1)

        if tenant_id:
            request.state.tenant_id = tenant_id
            logger.debug("Resolved tenant_id: %s", tenant_id)
        else:
            request.state.tenant_id = None

        return await call_next(request)
