from contextlib import suppress
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.infrastructure.auth.jwt import JWTService
from app.infrastructure.auth.supabase_jwt import SupabaseJWTVerifier

security = HTTPBearer(auto_error=False)

_supabase_verifier = SupabaseJWTVerifier()
_jwt_service = JWTService()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            token = request.cookies.get("astra_access_token", "")
        request.state.user_id = None
        if token:
            payload = await _verify_token(token)
            if payload is not None:
                sub = payload.get("sub")
                if sub:
                    with suppress(ValueError):
                        request.state.user_id = UUID(sub)
        return await call_next(request)


async def _verify_token(token: str) -> dict | None:
    if _supabase_verifier.enabled:
        payload = await _supabase_verifier.verify_token(token)
        if payload is not None:
            return payload
    return _jwt_service.verify_token(token)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UUID | None:
    if credentials is None:
        return None
    payload = await _verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    try:
        return UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        ) from None


async def require_user_id(
    user_id: UUID | None = Depends(get_current_user_id),
) -> UUID:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        ) from None
    return user_id
