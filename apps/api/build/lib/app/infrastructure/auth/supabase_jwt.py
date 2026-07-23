"""Supabase JWT verification using JWKS."""

import logging
import time

import httpx
from jose import JWTError, jwt
from jose.backends import RSAKey
from jose.constants import Algorithms

from app.config import config

logger = logging.getLogger(__name__)

JWKS_CACHE_TTL_SECONDS = 3600  # 1 hour


class SupabaseJWTVerifier:
    """Verifies JWTs issued by Supabase Auth using the JWKS endpoint."""

    def __init__(self) -> None:
        self._jwks: dict | None = None
        self._jwks_fetched_at: float = 0
        self._jwks_url = (
            f"{config.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            if config.supabase_url
            else ""
        )

    @property
    def enabled(self) -> bool:
        return bool(config.supabase_url and config.supabase_anon_key and self._jwks_url)

    async def _fetch_jwks(self) -> dict | None:
        now = time.monotonic()
        if self._jwks is not None and (now - self._jwks_fetched_at) < JWKS_CACHE_TTL_SECONDS:
            return self._jwks
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self._jwks_url)
                resp.raise_for_status()
                self._jwks = resp.json()
                self._jwks_fetched_at = now
                return self._jwks
        except Exception as e:
            logger.warning("Failed to fetch Supabase JWKS: %s", e)
            if self._jwks is not None:
                logger.info("Using stale JWKS cache due to fetch failure")
                return self._jwks
            return None

    async def verify_token(self, token: str) -> dict | None:
        jwks = await self._fetch_jwks()
        if jwks is None:
            return None

        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if kid is None:
            return None

        key_data = self._find_key(jwks, kid)
        if key_data is None:
            logger.debug("JWKS key with kid=%s not found, attempting refresh", kid)
            self._jwks = None
            self._jwks_fetched_at = 0
            jwks = await self._fetch_jwks()
            if jwks is None:
                return None
            key_data = self._find_key(jwks, kid)
            if key_data is None:
                return None

        public_key = RSAKey(key_data, Algorithms.RS256)
        try:
            return jwt.decode(
                token,
                public_key,
                algorithms=[Algorithms.RS256],
                audience="authenticated",
                options={"verify_exp": True},
            )
        except JWTError:
            return None

    @staticmethod
    def _find_key(jwks: dict, kid: str) -> dict | None:
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None
