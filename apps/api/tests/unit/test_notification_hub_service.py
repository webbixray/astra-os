from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.notifications.notification_hub_service import (
    NotificationHubService,
    _notification_streams,
)
from app.domain.entities.notifications.notification import (
    BroadcastAnnouncement,
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
)
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


@pytest.fixture
def notif_repo():
    return MagicMock()


@pytest.fixture
def template_repo():
    return MagicMock()


@pytest.fixture
def pref_repo():
    return MagicMock()


@pytest.fixture
def announcement_repo():
    return MagicMock()


@pytest.fixture
def service(notif_repo, template_repo, pref_repo, announcement_repo):
    return NotificationHubService(
        notif_repo=notif_repo,
        template_repo=template_repo,
        pref_repo=pref_repo,
        announcement_repo=announcement_repo,
    )


class TestSend:
    async def test_send_notification(self, service, notif_repo, pref_repo):
        pref_repo.find_by_user_and_type = AsyncMock(return_value=None)
        notif_repo.save = AsyncMock(return_value=Notification(
            id=uuid4(), type="campaign_milestone", title="Campaign Launched",
        ))

        result = await service.send(
            organization_id=uuid4(), user_id=uuid4(),
            type="campaign_milestone", title="Campaign Launched",
        )

        assert result.title == "Campaign Launched"
        notif_repo.save.assert_awaited_once()

    async def test_send_invalid_type(self, service):
        with pytest.raises(ValidationError, match="Unknown notification type"):
            await service.send(
                organization_id=uuid4(), user_id=uuid4(),
                type="invalid_type", title="Test",
            )

    async def test_send_invalid_channel(self, service):
        with pytest.raises(ValidationError, match="Unknown channel"):
            await service.send(
                organization_id=uuid4(), user_id=uuid4(),
                type="campaign_milestone", title="Test",
                channel="invalid_channel",
            )

    async def test_send_disabled_by_preference(self, service, pref_repo):
        pref = MagicMock()
        pref.enabled = False
        pref_repo.find_by_user_and_type = AsyncMock(return_value=pref)

        with pytest.raises(ValidationError, match="disabled by user"):
            await service.send(
                organization_id=uuid4(), user_id=uuid4(),
                type="campaign_milestone", title="Test",
            )

    async def test_send_with_email_channel(self, service, notif_repo, pref_repo):
        pref_repo.find_by_user_and_type = AsyncMock(return_value=None)
        notif_repo.save = AsyncMock(return_value=Notification(
            id=uuid4(), type="campaign_milestone", title="Test",
        ))

        with patch("app.application.use_cases.notifications.notification_hub_service.get_delivery_adapter") as mock_get:
            adapter = MagicMock()
            adapter.deliver = AsyncMock()
            mock_get.return_value = adapter

            await service.send(
                organization_id=uuid4(), user_id=uuid4(),
                type="campaign_milestone", title="Test",
                channel="email",
            )

            adapter.deliver.assert_awaited_once()

    async def test_send_pushes_to_sse_stream(self, service, notif_repo, pref_repo):
        pref_repo.find_by_user_and_type = AsyncMock(return_value=None)
        user_id = uuid4()
        notif_id = uuid4()
        notif_repo.save = AsyncMock(return_value=Notification(
            id=notif_id, type="campaign_milestone", title="Test",
        ))

        queue = MagicMock()
        _notification_streams[user_id] = [queue]

        await service.send(
            organization_id=uuid4(), user_id=user_id,
            type="campaign_milestone", title="Test",
        )

        queue.put_nowait.assert_called_once()
        _notification_streams.pop(user_id, None)


class TestSendFromTemplate:
    async def test_send_from_template(self, service, template_repo):
        template_id = uuid4()
        template = MagicMock(spec=NotificationTemplate)
        template.title_template = "Hello {{name}}"
        template.body_template = "Welcome {{name}} to {{org}}"
        template.type = "campaign_milestone"
        template.channel = "in_app"
        template_repo.find_by_id = AsyncMock(return_value=template)

        with patch.object(service, "send", AsyncMock(return_value=Notification(id=uuid4()))):
            result = await service.send_from_template(
                organization_id=uuid4(), user_id=uuid4(),
                template_id=template_id,
                variables={"name": "Alice", "org": "Acme"},
            )

            assert result is not None
            _, kwargs = service.send.await_args
            assert kwargs["title"] == "Hello Alice"
            assert kwargs["body"] == "Welcome Alice to Acme"

    async def test_send_from_template_not_found(self, service, template_repo):
        template_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.send_from_template(
                organization_id=uuid4(), user_id=uuid4(),
                template_id=uuid4(), variables={},
            )


class TestListNotifications:
    async def test_list_notifications(self, service, notif_repo):
        n = MagicMock(spec=Notification)
        n.id = uuid4()
        n.type = "campaign_milestone"
        n.title = "Campaign Launched"
        n.body = "Your campaign is live"
        n.resource_type = "campaign"
        n.resource_id = str(uuid4())
        n.channel = "in_app"
        n.is_read = False
        n.read_at = None
        n.archived = False
        n.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        notif_repo.find_by_user = AsyncMock(return_value=[n])
        notif_repo.count_by_user = AsyncMock(return_value=1)

        result = await service.list_notifications(
            user_id=uuid4(), organization_id=uuid4(),
        )

        assert result["total"] == 1
        assert result["items"][0]["title"] == "Campaign Launched"


class TestNotificationOperations:
    async def test_get_unread_count(self, service, notif_repo):
        notif_repo.count_unread = AsyncMock(return_value=5)

        result = await service.get_unread_count(uuid4(), uuid4())

        assert result == 5

    async def test_mark_read(self, service, notif_repo):
        notif_repo.mark_read = AsyncMock()

        await service.mark_read(uuid4())

        notif_repo.mark_read.assert_awaited_once()

    async def test_mark_all_read(self, service, notif_repo):
        notif_repo.mark_all_read = AsyncMock(return_value=3)

        result = await service.mark_all_read(uuid4(), uuid4())

        assert result == 3

    async def test_archive_notification(self, service, notif_repo):
        notif_repo.archive = AsyncMock()

        await service.archive_notification(uuid4())

        notif_repo.archive.assert_awaited_once()

    async def test_search_notifications(self, service, notif_repo):
        n = MagicMock(spec=Notification)
        n.id = uuid4()
        n.type = "campaign_milestone"
        n.title = "Found result"
        n.body = "details"
        n.channel = "in_app"
        n.is_read = False
        n.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        notif_repo.search = AsyncMock(return_value=[n])

        result = await service.search_notifications(
            user_id=uuid4(), organization_id=uuid4(), q="campaign",
        )

        assert len(result) == 1
        assert result[0]["title"] == "Found result"


class TestTemplates:
    async def test_create_template(self, service, template_repo):
        template_repo.save = AsyncMock(return_value=NotificationTemplate(
            id=uuid4(), name="Template", type="campaign_milestone",
            channel="in_app", title_template="Hello", body_template="World",
        ))

        result = await service.create_template(
            org_id=uuid4(), name="Template", type="campaign_milestone",
            channel="in_app", title_template="Hello", body_template="World",
        )

        assert result.name == "Template"

    async def test_create_template_invalid_type(self, service):
        with pytest.raises(ValidationError, match="Unknown type"):
            await service.create_template(
                org_id=uuid4(), name="T", type="bad", channel="in_app",
                title_template="Hello", body_template="World",
            )

    async def test_create_template_invalid_channel(self, service):
        with pytest.raises(ValidationError, match="Unknown channel"):
            await service.create_template(
                org_id=uuid4(), name="T", type="campaign_milestone",
                channel="bad", title_template="Hello",
            )

    async def test_list_templates(self, service, template_repo):
        t = MagicMock(spec=NotificationTemplate)
        t.id = uuid4()
        t.name = "Template"
        t.type = "campaign_milestone"
        t.channel = "in_app"
        t.variables = ["name"]
        t.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        template_repo.find_by_org = AsyncMock(return_value=[t])

        result = await service.list_templates(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Template"

    async def test_get_template(self, service, template_repo):
        template_id = uuid4()
        template_repo.find_by_id = AsyncMock(return_value=NotificationTemplate(
            id=template_id, name="Template",
        ))

        result = await service.get_template(template_id)

        assert result.name == "Template"

    async def test_get_template_not_found(self, service, template_repo):
        template_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.get_template(uuid4())

    async def test_delete_template(self, service, template_repo):
        template_repo.delete = AsyncMock()

        await service.delete_template(uuid4())

        template_repo.delete.assert_awaited_once()


class TestPreferences:
    async def test_set_preference(self, service, pref_repo):
        pref_repo.upsert = AsyncMock(return_value=UserNotificationPreference(
            user_id=uuid4(), notification_type="campaign_milestone",
            channel="in_app", enabled=True,
        ))

        result = await service.set_preference(
            user_id=uuid4(), notification_type="campaign_milestone",
            channel="in_app", enabled=True,
        )

        assert result.enabled is True

    async def test_get_preferences(self, service, pref_repo):
        p = MagicMock(spec=UserNotificationPreference)
        p.id = uuid4()
        p.notification_type = "campaign_milestone"
        p.channel = "in_app"
        p.enabled = True
        pref_repo.find_by_user = AsyncMock(return_value=[p])

        result = await service.get_preferences(uuid4())

        assert len(result) == 1
        assert result[0]["enabled"] is True


class TestAnnouncements:
    async def test_create_announcement(self, service, announcement_repo):
        announcement_repo.save = AsyncMock(return_value=BroadcastAnnouncement(
            id=uuid4(), title="System Update", severity="info",
        ))

        result = await service.create_announcement(
            org_id=uuid4(), title="System Update", severity="info",
        )

        assert result.title == "System Update"

    async def test_create_announcement_invalid_severity(self, service):
        with pytest.raises(ValidationError, match="Unknown severity"):
            await service.create_announcement(
                org_id=uuid4(), title="Test", severity="critical",
            )

    async def test_list_announcements(self, service, announcement_repo):
        a = MagicMock(spec=BroadcastAnnouncement)
        a.id = uuid4()
        a.title = "Update"
        a.body = "Details"
        a.severity = "info"
        a.target_role = ""
        a.dismissed_by = []
        a.expires_at = None
        a.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        announcement_repo.find_by_org = AsyncMock(return_value=[a])

        result = await service.list_announcements(uuid4())

        assert len(result) == 1
        assert result[0]["expired"] is False

    async def test_dismiss_announcement(self, service, announcement_repo):
        announcement_repo.add_dismissed = AsyncMock()

        await service.dismiss_announcement(uuid4(), uuid4())

        announcement_repo.add_dismissed.assert_awaited_once()

    async def test_delete_announcement(self, service, announcement_repo):
        announcement_repo.delete = AsyncMock()

        await service.delete_announcement(uuid4())

        announcement_repo.delete.assert_awaited_once()


class TestSSEStream:
    def test_subscribe_creates_queue(self):
        user_id = uuid4()
        svc = NotificationHubService(
            notif_repo=MagicMock(), template_repo=MagicMock(),
            pref_repo=MagicMock(), announcement_repo=MagicMock(),
        )
        _notification_streams.clear()

        queue = svc.subscribe(user_id)

        assert queue is not None
        assert queue in _notification_streams[user_id]

    def test_unsubscribe_removes_queue(self):
        user_id = uuid4()
        svc = NotificationHubService(
            notif_repo=MagicMock(), template_repo=MagicMock(),
            pref_repo=MagicMock(), announcement_repo=MagicMock(),
        )
        _notification_streams.clear()
        queue = svc.subscribe(user_id)
        assert user_id in _notification_streams

        svc.unsubscribe(user_id, queue)

        assert user_id not in _notification_streams

    def test_subscribe_multiple_queues(self):
        user_id = uuid4()
        svc = NotificationHubService(
            notif_repo=MagicMock(), template_repo=MagicMock(),
            pref_repo=MagicMock(), announcement_repo=MagicMock(),
        )
        _notification_streams.clear()

        q1 = svc.subscribe(user_id)
        q2 = svc.subscribe(user_id)

        assert len(_notification_streams[user_id]) == 2
        assert q1 != q2
