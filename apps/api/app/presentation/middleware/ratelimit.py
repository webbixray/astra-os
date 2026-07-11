import logging
import time
from collections import OrderedDict

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.cache.redis import RedisCache

logger = logging.getLogger(__name__)


AUTH_PATHS = ("/api/v1/auth/signin", "/api/v1/auth/signup", "/api/v1/auth/refresh")

# Per-endpoint rate limits for expensive operations (requests per minute)
ENDPOINT_LIMITS: dict[str, int] = {
    "/api/v1/ai/generate": 20,
    "/api/v1/ai/rewrite": 20,
    "/api/v1/ai/seo-score": 30,
    "/api/v1/email/send": 10,
    "/api/v1/reports/export": 15,
    "/api/v1/content/generate": 20,
}

# Maximum number of distinct client keys to track in memory before eviction
_MAX_LOCAL_CLIENTS = 10_000


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
        self._local_windows: OrderedDict[str, list[float]] = OrderedDict()

    @property
    def redis_cache(self) -> RedisCache | None:
        if self._redis_cache is not None:
            return self._redis_cache
        try:
            return getattr(self.app, "state", None).redis  # type: ignore[union-attr]
        except AttributeError:
            return None

    def _resolve_limit(self, path: str) -> int:
        """Return the applicable rate limit for a given path."""
        if path.startswith(AUTH_PATHS):
            return self.auth_requests_per_minute
        for prefix, limit in ENDPOINT_LIMITS.items():
            if path.startswith(prefix):
                return limit
        return self.requests_per_minute

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(w) for w in self.whitelist_paths):
            return await call_next(request)

        client_key = str(getattr(request.state, "user_id", "")) or (request.client.host if request.client else "unknown")
        if client_key in {"unknown", ""}:
            client_key = f"ip:{request.client.host}" if request.client else "unknown"

        limit = self._resolve_limit(path)

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
            self._get_count_local(client_key)  # prunes stale entries
            self._local_windows.setdefault(client_key, []).append(time.time())
            self._local_windows.move_to_end(client_key)
            self._evict_local()

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
        window = self._local_windows.get(client_key, [])
        window[:] = [t for t in window if t > now - 60]
        if not window and client_key in self._local_windows:
            del self._local_windows[client_key]
        return len(window)

    def _evict_local(self) -> None:
        """Evict oldest entries when the map exceeds capacity."""
        while len(self._local_windows) > _MAX_LOCAL_CLIENTS:
            self._local_windows.popitem(last=False)
