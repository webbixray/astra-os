from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.entities.user import User
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.auth.jwt import JWTService, RefreshTokenStore
from app.infrastructure.auth.password import hash_password, verify_password
from app.infrastructure.metrics import users_signed_up

if TYPE_CHECKING:
    from redis.asyncio import Redis

    from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

logger = logging.getLogger(__name__)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{}[\]|;:',.<>?/~`]).+$"
)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
# In-memory fallback (used only when Redis is unavailable)
_failed_attempts: dict[str, list[float]] = {}
_locked_accounts: dict[str, float] = {}


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValidationError(f"Password must not exceed {PASSWORD_MAX_LENGTH} characters.")
    if not PASSWORD_PATTERN.match(password):
        raise ValidationError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )


class AuthService:
    def __init__(
        self,
        repo: UserRepositoryImpl,
        jwt_service: JWTService | None = None,
        redis_client: Redis | None = None,
    ):
        self.repo = repo
        self.jwt = jwt_service or JWTService()
        self._redis = redis_client

    # ── Account lockout (Redis-backed with in-memory fallback) ────────

    async def _check_account_lockout(self, email: str) -> None:
        if self._redis:
            locked_until = await self._redis.get(f"lockout:{email}")
            if locked_until is not None:
                remaining = int(float(locked_until) - time.time())
                if remaining > 0:
                    raise ValidationError(
                        f"Account is temporarily locked due to too many failed attempts. "
                        f"Try again in {remaining} seconds."
                    )
                await self._redis.delete(f"lockout:{email}", f"attempts:{email}")
        else:
            locked_until = _locked_accounts.get(email)
            if locked_until is not None:
                if time.time() < locked_until:
                    remaining = int(locked_until - time.time())
                    raise ValidationError(
                        f"Account is temporarily locked due to too many failed attempts. "
                        f"Try again in {remaining} seconds."
                    )
                _locked_accounts.pop(email, None)
                _failed_attempts.pop(email, None)

    async def _record_failed_attempt(self, email: str) -> None:
        now = time.time()
        if self._redis:
            key = f"attempts:{email}"
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - LOCKOUT_DURATION_SECONDS)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, LOCKOUT_DURATION_SECONDS)
            _, count, _ = await pipe.execute()
            if count >= MAX_FAILED_ATTEMPTS:
                await self._redis.set(
                    f"lockout:{email}",
                    str(now + LOCKOUT_DURATION_SECONDS),
                    ex=LOCKOUT_DURATION_SECONDS,
                )
                logger.warning("Account locked due to %d failed attempts: %s", count, email)
        else:
            attempts = _failed_attempts.get(email, [])
            attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
            attempts.append(now)
            _failed_attempts[email] = attempts
            if len(attempts) >= MAX_FAILED_ATTEMPTS:
                _locked_accounts[email] = now + LOCKOUT_DURATION_SECONDS
                logger.warning("Account locked due to %d failed attempts: %s", len(attempts), email)

    async def _clear_failed_attempts(self, email: str) -> None:
        if self._redis:
            await self._redis.delete(f"lockout:{email}", f"attempts:{email}")
        else:
            _failed_attempts.pop(email, None)
            _locked_accounts.pop(email, None)

    async def sign_up(self, email: str, password: str, name: str) -> dict:
        validate_password_strength(password)

        existing = await self.repo.find_by_email(email)
        if existing:
            raise ValidationError("Email already registered")

        pw_hash = hash_password(password)
        user = User.create(email=email, name=name, password_hash=pw_hash)
        saved = await self.repo.save(user)

        users_signed_up.inc()

        access = self.jwt.create_access_token(str(saved.id))
        refresh = self.jwt.create_refresh_token(str(saved.id))

        logger.info("User registered: %s (%s)", saved.id, saved.email)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.USER_SIGNED_UP,
                aggregate_id=str(saved.id),
                aggregate_type="user",
                data={"email": saved.email, "name": saved.name},
            )
        )

        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": {
                "id": str(saved.id),
                "email": saved.email,
                "name": saved.name,
                "avatar_url": saved.avatar_url,
                "created_at": saved.created_at.isoformat(),
                "updated_at": saved.updated_at.isoformat(),
            },
        }

    async def sign_in(self, email: str, password: str) -> dict:
        await self._check_account_lockout(email)

        user = await self.repo.find_by_email(email)
        if user is None:
            await self._record_failed_attempt(email)
            raise ValidationError("Invalid email or password")

        if not user.password_hash:
            await self._record_failed_attempt(email)
            raise ValidationError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            await self._record_failed_attempt(email)
            raise ValidationError("Invalid email or password")

        if not user.is_active:
            raise ValidationError("Account is deactivated")

        await self._clear_failed_attempts(email)

        access = self.jwt.create_access_token(str(user.id))
        refresh = self.jwt.create_refresh_token(str(user.id))

        logger.info("User signed in: %s", user.id)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.USER_SIGNED_IN,
                aggregate_id=str(user.id),
                aggregate_type="user",
            )
        )

        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        result = self.jwt.rotate_refresh_token(refresh_token)
        if result is None:
            raise ValidationError("Invalid or expired refresh token")

        new_access, new_refresh = result
        payload = self.jwt.verify_token(new_access)
        if payload is None:
            raise ValidationError("Failed to verify new access token")

        user_id = payload.get("sub")
        user = await self.repo.find_by_id(UUID(user_id))
        if user is None:
            raise EntityNotFoundError("User", str(user_id))
        if not user.is_active:
            raise ValidationError("Account is deactivated")

        logger.info("Token refreshed for user: %s", user.id)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        }

    async def logout(self, refresh_token: str) -> None:
        payload = self.jwt.verify_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            await RefreshTokenStore.revoke(refresh_token)
            logger.info("User logged out, refresh token revoked: sub=%s", payload.get("sub"))

    async def get_current_user(self, user_id: UUID) -> User:
        user = await self.repo.find_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", str(user_id))
        return user
