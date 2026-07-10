from datetime import datetime
from uuid import uuid4

from app.domain.entities.adplatforms.platform import AdAccount, AdCampaign, AdPlatform, AdStatus
from app.domain.entities.ai.chat import ChatMessage, ChatRequest, MessageRole
from app.domain.entities.notifications.notification import (
    ANNOUNCEMENT_SEVERITIES,
    NOTIFICATION_CHANNELS,
    NOTIFICATION_TYPES,
    BroadcastAnnouncement,
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
)
from app.domain.entities.reports.report_schedule import ReportSchedule


class TestNotification:
    def test_create_notification(self):
        n = Notification.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            type="campaign_milestone",
            title="Campaign hit 1000 clicks",
            body="Great job!",
            resource_type="campaign",
            resource_id="camp-123",
            channel="email",
        )
        assert n.type == "campaign_milestone"
        assert n.title == "Campaign hit 1000 clicks"
        assert n.channel == "email"
        assert n.is_read is False
        assert n.archived is False

    def test_mark_read(self):
        n = Notification.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            type="general",
            title="Test",
        )
        n.mark_read()
        assert n.is_read is True
        assert n.read_at is not None

    def test_mark_read_idempotent(self):
        n = Notification.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            type="general",
            title="Test",
        )
        n.mark_read()
        first_read = n.read_at
        n.mark_read()  # Should not raise, should remain read
        assert n.is_read is True
        assert n.read_at >= first_read  # Timestamp may be updated

    def test_archive(self):
        n = Notification.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            type="general",
            title="Test",
        )
        n.archive()
        assert n.archived is True

    def test_all_types_defined(self):
        assert len(NOTIFICATION_TYPES) == 9
        assert "campaign_milestone" in NOTIFICATION_TYPES
        assert "approval_request" in NOTIFICATION_TYPES

    def test_all_channels_defined(self):
        assert NOTIFICATION_CHANNELS == ["in_app", "email", "sms", "slack"]

    def test_all_severities_defined(self):
        assert ANNOUNCEMENT_SEVERITIES == ["info", "warning", "error"]


class TestNotificationTemplate:
    def test_create_template(self):
        t = NotificationTemplate(
            organization_id=uuid4(),
            name="Campaign Launch",
            type="campaign_milestone",
            channel="email",
            title_template="Campaign {{name}} launched",
            body_template="Your campaign {{name}} has launched!",
            variables=["name"],
        )
        assert t.name == "Campaign Launch"
        assert t.variables == ["name"]


class TestUserNotificationPreference:
    def test_defaults(self):
        p = UserNotificationPreference(user_id=uuid4())
        assert p.notification_type == "general"
        assert p.channel == "in_app"
        assert p.enabled is True


class TestBroadcastAnnouncement:
    def test_create_announcement(self):
        a = BroadcastAnnouncement(
            organization_id=uuid4(),
            title="Maintenance",
            body="Scheduled downtime",
            severity="warning",
            target_role="admin",
            created_by=uuid4(),
        )
        assert a.severity == "warning"
        assert a.target_role == "admin"
        assert a.dismissed_by == []


class TestAdPlatforms:
    def test_ad_campaign_defaults(self):
        c = AdCampaign()
        assert c.platform == AdPlatform.GOOGLE_ADS
        assert c.status == AdStatus.DRAFT
        assert c.budget == 0
        assert c.currency == "USD"
        assert c.spend == 0

    def test_ad_account_defaults(self):
        a = AdAccount(organization_id=uuid4())
        assert a.platform == AdPlatform.GOOGLE_ADS
        assert a.is_connected is False
        assert a.credentials == {}

    def test_platforms_enum(self):
        assert AdPlatform.GOOGLE_ADS == "google_ads"
        assert AdPlatform.META == "meta"
        assert AdPlatform.LINKEDIN == "linkedin"
        assert AdPlatform.TIKTOK == "tiktok"
        assert AdPlatform.TWITTER == "twitter"

    def test_ad_statuses(self):
        assert AdStatus.DRAFT == "draft"
        assert AdStatus.ACTIVE == "active"
        assert AdStatus.PAUSED == "paused"


class TestChatMessage:
    def test_create_with_defaults(self):
        m = ChatMessage(role=MessageRole.USER, content="Hello")
        assert m.role == MessageRole.USER
        assert m.content == "Hello"
        assert m.id is not None
        assert m.timestamp is not None

    def test_create_with_custom_id_and_timestamp(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        m = ChatMessage(role=MessageRole.ASSISTANT, content="Hi", id="custom-id", timestamp=ts)
        assert m.id == "custom-id"
        assert m.timestamp == ts

    def test_to_dict_excludes_id_and_timestamp(self):
        m = ChatMessage(role=MessageRole.SYSTEM, content="System prompt", id="x", timestamp=datetime.now())
        d = m.to_dict()
        assert d == {"role": "system", "content": "System prompt"}
        assert "id" not in d
        assert "timestamp" not in d

    def test_roles(self):
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"


class TestChatRequest:
    def test_create_with_defaults(self):
        r = ChatRequest(
            organization_id="org-1",
            user_id="user-1",
            message="Hello",
        )
        assert r.organization_id == "org-1"
        assert r.user_id == "user-1"
        assert r.message == "Hello"
        assert r.conversation_id is not None
        assert r.page_context == {}
        assert r.messages == []

    def test_create_with_all_fields(self):
        msgs = [ChatMessage(role=MessageRole.USER, content="Hi")]
        r = ChatRequest(
            organization_id="org-1",
            user_id="user-1",
            message="Hello",
            conversation_id="conv-123",
            page_context={"page": "campaign"},
            messages=msgs,
        )
        assert r.conversation_id == "conv-123"
        assert r.page_context == {"page": "campaign"}
        assert r.messages == msgs


class TestReportSchedule:
    def test_create_schedule(self):
        s = ReportSchedule.create(
            organization_id=uuid4(),
            name="Weekly Report",
            report_type="overview",
            frequency="weekly",
            recipients=["a@b.com", "c@d.com"],
            config={"filters": {"date_range": "last_week"}},
            created_by=uuid4(),
        )
        assert s.name == "Weekly Report"
        assert s.report_type == "overview"
        assert s.frequency == "weekly"
        assert s.recipients == ["a@b.com", "c@d.com"]
        assert s.config == {"filters": {"date_range": "last_week"}}
        assert s.is_active is True
        assert s.next_run_at is None
        assert s.last_run_at is None

    def test_defaults(self):
        s = ReportSchedule.create(organization_id=uuid4(), name="X")
        assert s.report_type == "overview"
        assert s.frequency == "weekly"
        assert s.recipients == []
        assert s.config == {}
        assert s.created_by is None
