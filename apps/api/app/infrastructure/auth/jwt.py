from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

from jose import JWTError, jwt
from pydantic_settings import BaseSettings

from app.config import config as app_config

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[None]] = set()


class JWTConfig(BaseSettings):
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    issuer: str = "astra-os"
    audience: str = "astra-api"
    token_version: int = 1

    model_config = {"env_prefix": "jwt_"}

    @property
    def effective_secret(self) -> str:
        return self.secret_key or app_config.secret_key


class RefreshTokenStore:
    _redis: ClassVar[Any] = None
    _memory_revoked: ClassVar[set[str]] = set()
    _memory_fingerprints: ClassVar[dict[str, str]] = {}
    _KEY_PREFIX_REVOKED: ClassVar[str] = "astra:refresh:revoked:"
    _KEY_PREFIX_FP: ClassVar[str] = "astra:refresh:fp:"
    _TTL_SECONDS: ClassVar[int] = 7 * 24 * 3600

    @classmethod
    def _get_redis(cls) -> Any:
        if cls._redis is not None:
            return cls._redis
        try:
            import redis.asyncio as aioredis

            cls._redis = aioredis.from_url(
                app_config.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        except Exception:
            logger.debug("Redis unavailable for RefreshTokenStore, using in-memory fallback")
            return None
        else:
            return cls._redis

    @classmethod
    def fingerprint(cls, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    async def revoke(cls, token: str) -> None:
        fp = cls.fingerprint(token)
        redis = cls._get_redis()
        if redis is not None:
            try:
                await redis.set(cls._KEY_PREFIX_REVOKED + fp, "1", ex=cls._TTL_SECONDS)
            except Exception:
                logger.warning("Failed to store revoked token in Redis, using in-memory")
        cls._memory_revoked.add(fp)

    @classmethod
    async def is_revoked(cls, token: str) -> bool:
        fp = cls.fingerprint(token)
        redis = cls._get_redis()
        if redis is not None:
            try:
                return await redis.exists(cls._KEY_PREFIX_REVOKED + fp) > 0
            except Exception:
                logger.warning("Failed to check revoked token in Redis, using in-memory")
        return fp in cls._memory_revoked

    @classmethod
    async def register(cls, token: str, user_id: str) -> None:
        fp = cls.fingerprint(token)
        redis = cls._get_redis()
        if redis is not None:
            try:
                await redis.set(cls._KEY_PREFIX_FP + fp, user_id, ex=cls._TTL_SECONDS)
            except Exception:
                logger.warning("Failed to register token in Redis, using in-memory")
                cls._memory_fingerprints[fp] = user_id
            else:
                return
        cls._memory_fingerprints[fp] = user_id


class JWTService:
    def __init__(self, config: JWTConfig | None = None):
        self.config = config or JWTConfig()

    def _sign_payload(self, payload: dict) -> str:
        return jwt.encode(
            payload,
            self.config.effective_secret,
            algorithm=self.config.algorithm,
        )

    def create_access_token(self, user_id: str, extra_claims: dict | None = None) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.config.access_token_expire_minutes),
            "type": "access",
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "jti": hashlib.sha256(f"{user_id}:{now.isoformat()}".encode()).hexdigest()[:16],
            "ver": self.config.token_version,
        }
        if extra_claims:
            payload.update(extra_claims)
        return self._sign_payload(payload)

    def create_refresh_token(self, user_id: str) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(days=self.config.refresh_token_expire_days),
            "type": "refresh",
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "jti": hashlib.sha256(f"refresh:{user_id}:{now.isoformat()}".encode()).hexdigest()[:16],
            "ver": self.config.token_version,
        }
        token = self._sign_payload(payload)
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(RefreshTokenStore.register(token, user_id))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
        except RuntimeError:
            pass
        return token

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token,
                self.config.effective_secret,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={"verify_exp": True, "verify_iat": True},
            )
            if payload.get("type") == "refresh":
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        revoked = (
                            RefreshTokenStore.fingerprint(token)
                            in RefreshTokenStore._memory_revoked
                        )
                    else:
                        revoked = loop.run_until_complete(RefreshTokenStore.is_revoked(token))
                except RuntimeError:
                    revoked = (
                        RefreshTokenStore.fingerprint(token) in RefreshTokenStore._memory_revoked
                    )
                if revoked:
                    logger.warning(
                        "Attempted use of revoked refresh token: sub=%s", payload.get("sub")
                    )
                    return None
        except JWTError as e:
            logger.debug("JWT verification failed: %s", e)
            return None
        else:
            return payload

    def rotate_refresh_token(self, old_token: str) -> tuple[str, str] | None:
        payload = self.verify_token(old_token)
        if payload is None or payload.get("type") != "refresh":
            return None
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(RefreshTokenStore.revoke(old_token))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
        except RuntimeError:
            RefreshTokenStore._memory_revoked.add(RefreshTokenStore.fingerprint(old_token))
        user_id = payload["sub"]
        new_access = self.create_access_token(user_id)
        new_refresh = self.create_refresh_token(user_id)
        return new_access, new_refresh
