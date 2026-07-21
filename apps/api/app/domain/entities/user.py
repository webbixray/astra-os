from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.exceptions.domain_exceptions import ValidationError


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""
    avatar_url: str | None = None
    password_hash: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, email: str, name: str, password_hash: str = "") -> "User":  # nosec B107
        if not email or not email.strip():
            raise ValidationError("Email is required")
        if "@" not in email:
            raise ValidationError("Invalid email format")
        if not name or not name.strip():
            raise ValidationError("Name is required")
        return cls(
            email=email.strip(),
            name=name.strip(),
            password_hash=password_hash,
        )

    def update_profile(self, name: str | None = None, avatar_url: str | None = None) -> None:
        if name is not None:
            self.name = name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def set_password_hash(self, password_hash: str) -> None:
        self.password_hash = password_hash
        self.updated_at = datetime.now(UTC)

    def to_safe_dict(self) -> dict:
        """Return user data dict excluding sensitive fields like password_hash."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
