from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

PUBLISH_PLATFORMS = ["website", "twitter", "linkedin", "facebook", "instagram", "email"]
PUBLISH_STATUSES = ["scheduled", "publishing", "published", "failed"]


@dataclass
class ContentPublish:
    id: UUID = field(default_factory=uuid4)
    content_id: UUID = field(default_factory=uuid4)
    platform: str = ""
    status: str = "scheduled"
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    external_url: str | None = None
    error_message: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        content_id: UUID,
        platform: str,
        scheduled_at: datetime | None = None,
        metadata: dict | None = None,
    ) -> "ContentPublish":
        if platform not in PUBLISH_PLATFORMS:
            raise ValidationError(f"Invalid platform: {platform}. Must be one of {PUBLISH_PLATFORMS}")
        return cls(
            content_id=content_id,
            platform=platform,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
        )

    def mark_publishing(self) -> None:
        self.status = "publishing"
        self.updated_at = now()

    def mark_published(self, external_url: str | None = None) -> None:
        self.status = "published"
        self.published_at = now()
        self.external_url = external_url
        self.updated_at = now()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error
        self.updated_at = now()
