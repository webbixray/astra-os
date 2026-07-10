import logging
import time

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.cache.redis import RedisCache

logger = logging.getLogger(__name__)


AUTH_PATHS = ("/api/v1/auth/signin", "/api/v1/auth/signup", "/api/v1/auth/refresh")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 120,
        auth_requests_per_minute: int = 10,
        whitelist_paths: list[str] | None = None,
        redis_cache: RedisCache | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.whitelist_paths = whitelist_paths or ["/api/v1/health"]
        self._redis_cache = redis_cache
        self._local_windows: dict[str, list[float]] = {}

    @property
    def redis_cache(self) -> RedisCache | None:
        if self._redis_cache is not None:
            return self._redis_cache
        try:
            return getattr(self.app, "state", None).redis  # type: ignore[union-attr]
        except AttributeError:
            return None

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(w) for w in self.whitelist_paths):
            return await call_next(request)

        client_key = str(getattr(request.state, "user_id", "")) or (request.client.host if request.client else "unknown")
        if client_key in {"unknown", ""}:
            client_key = f"ip:{request.client.host}" if request.client else "unknown"

        is_auth = path.startswith(AUTH_PATHS)
        limit = self.auth_requests_per_minute if is_auth else self.requests_per_minute

        if self.redis_cache and self.redis_cache.client is not None:
            count = await self._get_count_redis(client_key)
        else:
            count = self._get_count_local(client_key)

        remaining = max(0, limit - count)
        reset_at = self._get_reset_time()

        if count >= limit:
            logger.warning("Rate limit exceeded for %s (path: %s)", client_key, path)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "code": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        if self.redis_cache and self.redis_cache.client is not None:
            await self._increment_redis(client_key)
        else:
            self._local_windows.setdefault(client_key, []).append(time.time())

        response = await call_next(request)
        self._add_rate_limit_headers(response, limit, remaining, reset_at)
        return response

    def _add_rate_limit_headers(self, response: Response, limit: int, remaining: int, reset_at: int) -> None:
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

    def _get_reset_time(self) -> int:
        now = int(time.time())
        return now + (60 - (now % 60))

    async def _get_count_redis(self, client_key: str) -> int:
        now = int(time.time())
        window_key = f"ratelimit:{client_key}:{now // 60}"
        count = await self.redis_cache.client.get(window_key)
        return int(count) if count else 0

    async def _increment_redis(self, client_key: str) -> None:
        now = int(time.time())
        window_key = f"ratelimit:{client_key}:{now // 60}"
        count = await self.redis_cache.client.incr(window_key)
        if count == 1:
            await self.redis_cache.client.expire(window_key, 60)

    def _get_count_local(self, client_key: str) -> int:
        now = time.time()
        window = self._local_windows.setdefault(client_key, [])
        window[:] = [t for t in window if t > now - 60]
        return len(window)

    def _check_local(self, client_key: str, limit: int) -> bool:
        now = time.time()
        window = self._local_windows.setdefault(client_key, [])
        window[:] = [t for t in window if t > now - 60]
        if len(window) >= limit:
            return False
        window.append(now)
        return True
