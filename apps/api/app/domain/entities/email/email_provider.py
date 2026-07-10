from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

EMAIL_PROVIDER_TYPES = ["sendgrid", "ses", "smtp"]


@dataclass
class EmailProvider:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    provider_type: str = "sendgrid"
    name: str = ""
    api_key: str = ""
    from_email: str = ""
    from_name: str = ""
    is_verified: bool = False
    is_active: bool = True
    config: dict = field(default_factory=dict)
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        provider_type: str,
        name: str,
        api_key: str,
        from_email: str,
        created_by: UUID,
        from_name: str = "",
        config: dict | None = None,
    ) -> "EmailProvider":
        if provider_type not in EMAIL_PROVIDER_TYPES:
            raise ValidationError(f"Invalid provider type: {provider_type}")
        if not api_key:
            raise ValidationError("API key is required")
        if not from_email or "@" not in from_email:
            raise ValidationError("Valid from email is required")
        return cls(
            organization_id=organization_id,
            provider_type=provider_type,
            name=name,
            api_key=api_key,
            from_email=from_email,
            from_name=from_name,
            created_by=created_by,
            config=config or {},
        )
