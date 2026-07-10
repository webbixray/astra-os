from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


@dataclass
class Content:
    id: UUID = field(default_factory=uuid4)
    campaign_id: UUID | None = None
    organization_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content_type: str = "blog"
    body: str = ""
    status: str = "draft"
    brand_profile_id: UUID | None = None
    generated_by_ai: bool = False
    version: int = 1
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    VALID_TYPES: ClassVar[list[str]] = ["blog", "social", "email", "ad", "landing", "video_desc"]
    VALID_STATUSES: ClassVar[list[str]] = ["draft", "review", "approved", "published", "archived"]

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        title: str,
        content_type: str,
        created_by: UUID,
        *,
        campaign_id: UUID | None = None,
        body: str = "",
        brand_profile_id: UUID | None = None,
        generated_by_ai: bool = False,
    ) -> "Content":
        instance = cls(
            organization_id=organization_id,
            title=title,
            content_type=content_type,
            created_by=created_by,
            campaign_id=campaign_id,
            body=body,
            brand_profile_id=brand_profile_id,
            generated_by_ai=generated_by_ai,
        )
        instance._validate()
        return instance

    def _validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValidationError("Content title is required")
        if self.content_type not in self.VALID_TYPES:
            raise ValidationError(
                f"Invalid content type: {self.content_type}. Must be one of {self.VALID_TYPES}"
            )

    def update_body(self, body: str) -> None:
        self.body = body
        self.version += 1
        self.updated_at = now()

    def submit_for_review(self) -> None:
        if self.status != "draft":
            raise ValidationError(f"Cannot submit content in status '{self.status}' for review")
        self.status = "review"
        self.updated_at = now()

    def approve(self) -> None:
        if self.status != "review":
            raise ValidationError(f"Cannot approve content in status '{self.status}'")
        self.status = "approved"
        self.updated_at = now()

    def publish(self) -> None:
        if self.status != "approved":
            raise ValidationError(f"Cannot publish content in status '{self.status}'")
        self.status = "published"
        self.published_at = now()
        self.updated_at = now()

    def request_changes(self) -> None:
        if self.status != "review":
            raise ValidationError(f"Cannot request changes for content in status '{self.status}'")
        self.status = "draft"
        self.updated_at = now()
