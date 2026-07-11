from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

NOTIFICATION_TYPES = [
    "campaign_milestone",
    "approval_request",
    "workflow_completed",
    "workflow_failed",
    "ad_sync_completed",
    "content_published",
    "member_joined",
    "report_ready",
    "campaign_status_changed",
]

NOTIFICATION_CHANNELS = ["in_app", "email", "sms", "slack"]

ANNOUNCEMENT_SEVERITIES = ["info", "warning", "error"]


@dataclass
class Notification:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    type: str = "general"
    title: str = ""
    body: str = ""
    resource_type: str = ""
    resource_id: str = ""
    channel: str = "in_app"
    template_id: UUID | None = None
    is_read: bool = False
    read_at: datetime | None = None
    archived: bool = False
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        body: str = "",
        resource_type: str = "",
        resource_id: str = "",
        channel: str = "in_app",
        template_id: UUID | None = None,
    ) -> "Notification":
        if type not in NOTIFICATION_TYPES:
            raise ValidationError(
                f"Invalid notification type: {type}. Must be one of {NOTIFICATION_TYPES}"
            )
        if channel not in NOTIFICATION_CHANNELS:
            raise ValidationError(
                f"Invalid notification channel: {channel}. Must be one of {NOTIFICATION_CHANNELS}"
            )
        if not title or not title.strip():
            raise ValidationError("Notification title is required")
        return cls(
            organization_id=organization_id,
            user_id=user_id,
            type=type,
            title=title.strip(),
            body=body,
            resource_type=resource_type,
            resource_id=resource_id,
            channel=channel,
            template_id=template_id,
        )

    def mark_read(self) -> None:
        self.is_read = True
        self.read_at = now()

    def archive(self) -> None:
        self.archived = True


@dataclass
class NotificationTemplate:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    type: str = "general"
    channel: str = "in_app"
    title_template: str = ""
    body_template: str = ""
    variables: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)


@dataclass
class UserNotificationPreference:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    notification_type: str = "general"
    channel: str = "in_app"
    enabled: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)


@dataclass
class BroadcastAnnouncement:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    title: str = ""
    body: str = ""
    severity: str = "info"
    target_role: str = ""
    created_by: UUID = field(default_factory=uuid4)
    dismissed_by: list[UUID] = field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=now)
