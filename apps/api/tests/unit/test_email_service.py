from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.email.email_service import EmailService
from app.domain.entities.email.email_campaign import EmailCampaign
from app.domain.entities.email.email_event import EmailEvent
from app.domain.entities.email.email_provider import EmailProvider
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


@pytest.fixture
def provider_repo():
    return MagicMock()


@pytest.fixture
def campaign_repo():
    return MagicMock()


@pytest.fixture
def event_repo():
    return MagicMock()


@pytest.fixture
def service(provider_repo, campaign_repo, event_repo):
    return EmailService(
        provider_repo=provider_repo,
        campaign_repo=campaign_repo,
        event_repo=event_repo,
    )


def make_provider(**overrides):
    p = MagicMock(spec=EmailProvider)
    p.id = overrides.get("id", uuid4())
    p.organization_id = overrides.get("organization_id", uuid4())
    p.provider_type = overrides.get("provider_type", "sendgrid")
    p.name = overrides.get("name", "My Provider")
    p.api_key = overrides.get("api_key", "sk-123")
    p.from_email = overrides.get("from_email", "test@example.com")
    p.from_name = overrides.get("from_name", "")
    p.config = overrides.get("config", {})
    p.created_by = overrides.get("created_by", uuid4())
    return p


def make_campaign(**overrides):
    c = MagicMock(spec=EmailCampaign)
    c.id = overrides.get("id", uuid4())
    c.organization_id = overrides.get("organization_id", uuid4())
    c.provider_id = overrides.get("provider_id", uuid4())
    c.name = overrides.get("name", "Test Campaign")
    c.subject = overrides.get("subject", "Hello")
    c.body = overrides.get("body", "Body")
    c.from_email = overrides.get("from_email", "from@example.com")
    c.from_name = overrides.get("from_name", "")
    c.status = overrides.get("status", "draft")
    c.send = MagicMock()
    c.fail = MagicMock()
    c.complete = MagicMock()
    c.open_count = 0
    c.click_count = 0
    c.bounce_count = 0
    return c


class TestProviderManagement:
    async def test_create_provider(self, service, provider_repo):
        provider_repo.save = AsyncMock(
            return_value=EmailProvider(
                organization_id=uuid4(),
                provider_type="sendgrid",
                name="Provider",
                api_key="sk-123",
                from_email="t@t.com",
                created_by=uuid4(),
            )
        )

        result = await service.create_provider(
            uuid4(), "sendgrid", "Provider", "sk-123", "t@t.com", uuid4()
        )

        assert result.name == "Provider"

    async def test_list_providers(self, service, provider_repo):
        p = make_provider()
        provider_repo.find_by_organization = AsyncMock(return_value=[p])

        result = await service.list_providers(uuid4())

        assert len(result) == 1

    async def test_delete_provider(self, service, provider_repo):
        provider_repo.delete = AsyncMock()

        await service.delete_provider(uuid4())

        provider_repo.delete.assert_awaited_once()


class TestCampaignManagement:
    async def test_create_campaign(self, service, campaign_repo):
        campaign_repo.save = AsyncMock(
            return_value=EmailCampaign(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="Campaign",
                subject="Subject",
                body="Body",
                from_email="f@t.com",
                created_by=uuid4(),
            )
        )

        result = await service.create_campaign(
            uuid4(), uuid4(), "Campaign", "Subject", "Body", "f@t.com", uuid4()
        )

        assert result.name == "Campaign"

    async def test_create_campaign_with_schedule(self, service, campaign_repo):
        campaign_repo.save = AsyncMock(
            return_value=EmailCampaign(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="Campaign",
                subject="Subject",
                body="Body",
                from_email="f@t.com",
                created_by=uuid4(),
            )
        )

        result = await service.create_campaign(
            uuid4(),
            uuid4(),
            "Campaign",
            "Subject",
            "Body",
            "f@t.com",
            uuid4(),
            scheduled_at="2025-06-15T10:00:00+00:00",
        )

        assert result is not None

    async def test_list_campaigns(self, service, campaign_repo):
        c = make_campaign()
        campaign_repo.find_by_organization = AsyncMock(return_value=[c])

        result = await service.list_campaigns(uuid4())

        assert len(result) == 1

    async def test_list_campaigns_filtered(self, service, campaign_repo):
        c = make_campaign(status="sent")
        campaign_repo.find_by_organization = AsyncMock(return_value=[c])

        result = await service.list_campaigns(uuid4(), status="sent")

        assert result[0].status == "sent"

    async def test_get_campaign_found(self, service, campaign_repo):
        c = make_campaign()
        campaign_repo.find_by_id = AsyncMock(return_value=c)

        result = await service.get_campaign(uuid4())

        assert result == c

    async def test_get_campaign_not_found(self, service, campaign_repo):
        campaign_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.get_campaign(uuid4())


class TestSendCampaign:
    async def test_send_success(self, service, campaign_repo, provider_repo, event_repo):
        provider = make_provider(provider_type="sendgrid")
        campaign = make_campaign(provider_id=provider.id)
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        campaign_repo.save = AsyncMock(return_value=campaign)
        provider_repo.find_by_id = AsyncMock(return_value=provider)
        event_repo.save_all = AsyncMock()

        mock_sender = MagicMock()
        mock_sender.send = AsyncMock(return_value={"sent_count": 2})

        with patch(
            "app.application.use_cases.email.email_service.get_sender", return_value=mock_sender
        ):
            await service.send_campaign(campaign.id, ["a@b.com", "c@d.com"])

        campaign.send.assert_called_once()
        campaign.complete.assert_called_once_with(sent=2)
        event_repo.save_all.assert_awaited_once()
        assert len(event_repo.save_all.call_args[0][0]) == 2
        # Save is called: initial, after send, and maybe fail... actually
        # send() -> save, send_sender -> complete -> save, event -> save events
        assert campaign_repo.save.call_count >= 2

    async def test_send_campaign_not_found(self, service, campaign_repo):
        campaign_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.send_campaign(uuid4(), ["a@b.com"])

    async def test_send_provider_not_found(self, service, campaign_repo, provider_repo):
        campaign = make_campaign()
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        provider_repo.find_by_id = AsyncMock(return_value=None)
        campaign_repo.save = AsyncMock(return_value=campaign)

        await service.send_campaign(campaign.id, ["a@b.com"])

        campaign.fail.assert_called_once()

    async def test_send_sender_not_found(self, service, campaign_repo, provider_repo):
        provider = make_provider()
        campaign = make_campaign(provider_id=provider.id)
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        provider_repo.find_by_id = AsyncMock(return_value=provider)
        campaign_repo.save = AsyncMock(return_value=campaign)

        with patch("app.application.use_cases.email.email_service.get_sender", return_value=None):
            await service.send_campaign(campaign.id, ["a@b.com"])

        campaign.fail.assert_called_once()

    async def test_send_sender_error(self, service, campaign_repo, provider_repo):
        provider = make_provider()
        campaign = make_campaign(provider_id=provider.id)
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        provider_repo.find_by_id = AsyncMock(return_value=provider)
        campaign_repo.save = AsyncMock(return_value=campaign)

        mock_sender = MagicMock()
        mock_sender.send = AsyncMock(side_effect=RuntimeError("SMTP error"))

        with patch(
            "app.application.use_cases.email.email_service.get_sender", return_value=mock_sender
        ):
            await service.send_campaign(campaign.id, ["a@b.com"])

        campaign.fail.assert_called_once()


class TestAnalytics:
    async def test_get_analytics(self, service, campaign_repo):
        campaign_repo.get_analytics = AsyncMock(return_value={"total": 5, "sent": 3})

        result = await service.get_analytics(uuid4())

        assert result["total"] == 5


class TestEvents:
    async def test_get_campaign_events(self, service, event_repo):
        e = MagicMock(spec=EmailEvent)
        e.id = uuid4()
        e.event_type = "opened"
        e.recipient_email = "a@b.com"
        e.occurred_at = datetime(2025, 1, 1, 12, 0)
        event_repo.find_by_campaign = AsyncMock(return_value=[e])

        result = await service.get_campaign_events(uuid4())

        assert len(result) == 1
        assert result[0]["event_type"] == "opened"

    async def test_record_event_updates_campaign(self, service, event_repo, campaign_repo):
        event_repo.save = AsyncMock()
        campaign = make_campaign()
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        campaign_repo.save = AsyncMock()

        await service.record_event(uuid4(), "opened", "a@b.com")

        assert campaign.open_count == 1
        campaign_repo.save.assert_called()

    async def test_record_event_clicked(self, service, event_repo, campaign_repo):
        event_repo.save = AsyncMock()
        campaign = make_campaign()
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        campaign_repo.save = AsyncMock()

        await service.record_event(uuid4(), "clicked", "a@b.com")

        assert campaign.click_count == 1

    async def test_record_event_bounced(self, service, event_repo, campaign_repo):
        event_repo.save = AsyncMock()
        campaign = make_campaign()
        campaign_repo.find_by_id = AsyncMock(return_value=campaign)
        campaign_repo.save = AsyncMock()

        await service.record_event(uuid4(), "bounced", "a@b.com")

        assert campaign.bounce_count == 1

    async def test_record_event_campaign_not_found(self, service, event_repo, campaign_repo):
        event_repo.save = AsyncMock()
        campaign_repo.find_by_id = AsyncMock(return_value=None)

        await service.record_event(uuid4(), "opened", "a@b.com")

        event_repo.save.assert_awaited_once()

    async def test_delete_campaign(self, service, campaign_repo):
        campaign_repo.delete = AsyncMock()

        await service.delete_campaign(uuid4())

        campaign_repo.delete.assert_awaited_once()
