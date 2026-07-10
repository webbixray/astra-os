from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.entities.user import User
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.auth.jwt import JWTService, RefreshTokenStore
from app.infrastructure.auth.password import hash_password, verify_password
from app.infrastructure.metrics import users_signed_up

if TYPE_CHECKING:
    from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

logger = logging.getLogger(__name__)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{}[\]|;:',.<>?/~`]).+$"
)


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
        )
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValidationError(
            f"Password must not exceed {PASSWORD_MAX_LENGTH} characters."
        )
    if not PASSWORD_PATTERN.match(password):
        raise ValidationError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )


class AuthService:
    def __init__(self, repo: UserRepositoryImpl, jwt_service: JWTService | None = None):
        self.repo = repo
        self.jwt = jwt_service or JWTService()

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
        user = await self.repo.find_by_email(email)
        if user is None:
            raise ValidationError("Invalid email or password")

        if not user.password_hash:
            raise ValidationError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise ValidationError("Invalid email or password")

        if not user.is_active:
            raise ValidationError("Account is deactivated")

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
