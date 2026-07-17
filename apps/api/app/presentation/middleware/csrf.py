from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from typing import TYPE_CHECKING, Final

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import config

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)

SAFE_METHODS: Final[frozenset[str]] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
EXEMPT_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/api/v1/auth/signin",
        "/api/v1/auth/signup",
        "/api/v1/auth/refresh",
        "/api/v1/health",
    }
)


def _generate_csrf_token(secret: str, session_id: str, timestamp: int | None = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        msg.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{timestamp}:{signature}"


def _verify_csrf_token(token: str, secret: str, session_id: str, max_age: int = 7200) -> bool:
    try:
        parts = token.split(":")
        if len(parts) != 2:
            return False
        timestamp_str, _signature = parts
        timestamp = int(timestamp_str)
        if time.time() - timestamp > max_age:
            return False
        expected = _generate_csrf_token(secret, session_id, timestamp)
        return hmac.compare_digest(token, expected)
    except (ValueError, IndexError):
        return False


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str | None = None, cookie_name: str = "astra_csrf") -> None:
        super().__init__(app)
        self.secret = secret or config.secret_key
        self.cookie_name = cookie_name

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        if request.method in SAFE_METHODS:
            response = await call_next(request)
            if not request.cookies.get(self.cookie_name):
                session_id = secrets.token_urlsafe(16)
                csrf_token = _generate_csrf_token(self.secret, session_id)
                response.set_cookie(
                    key=self.cookie_name,
                    value=csrf_token,
                    httponly=False,
                    samesite="lax",
                    secure=config.is_production,
                    max_age=7200,
                )
                response.set_cookie(
                    key="astra_session",
                    value=session_id,
                    httponly=True,
                    samesite="lax",
                    secure=config.is_production,
                    max_age=7200,
                )
            return response

        csrf_cookie = request.cookies.get(self.cookie_name)
        csrf_header = request.headers.get("X-CSRF-Token")
        session_id = request.cookies.get("astra_session", "")

        if not csrf_cookie or not csrf_header or not session_id:
            logger.warning("CSRF validation failed: missing token (path=%s)", path)
            return JSONResponse(
                status_code=403,
                content={"success": False, "code": "csrf_error", "message": "CSRF token missing"},
            )

        if not _verify_csrf_token(csrf_cookie, self.secret, session_id):
            logger.warning("CSRF validation failed: invalid token (path=%s)", path)
            return JSONResponse(
                status_code=403,
                content={"success": False, "code": "csrf_error", "message": "CSRF token invalid"},
            )

        if not hmac.compare_digest(csrf_cookie, csrf_header):
            logger.warning("CSRF validation failed: cookie/header mismatch (path=%s)", path)
            return JSONResponse(
                status_code=403,
                content={"success": False, "code": "csrf_error", "message": "CSRF token mismatch"},
            )

        return await call_next(request)
