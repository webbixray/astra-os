from uuid import uuid4

import pytest

from app.domain.entities.content.content import Content
from app.domain.services.email.base_sender import EmailSender
from app.domain.services.email.senders import (
    SENDER_REGISTRY,
    SendGridSender,
    SESEmailSender,
    SMTPEmailSender,
    get_sender,
)
from app.domain.services.notifications.delivery_adapters import (
    EmailNotificationAdapter,
    NotificationDeliveryAdapter,
    SlackNotificationAdapter,
    SMSNotificationAdapter,
    get_delivery_adapter,
)
from app.domain.services.publishing.adapters import (
    ADAPTER_REGISTRY,
    EmailAdapter,
    FacebookAdapter,
    InstagramAdapter,
    LinkedInAdapter,
    TwitterAdapter,
    WebsiteAdapter,
    get_adapter,
)
from app.domain.services.publishing.base_adapter import PublishingAdapter
from app.domain.services.reporting.delivery_adapters import (
    EmailDeliveryAdapter as ReportEmailDeliveryAdapter,
)
from app.domain.services.reporting.delivery_adapters import (
    ReportDeliveryAdapter,
    WebhookDeliveryAdapter,
)
from app.domain.services.reporting.delivery_adapters import (
    SlackDeliveryAdapter as ReportSlackDeliveryAdapter,
)
from app.domain.services.reporting.delivery_adapters import (
    get_delivery_adapter as get_report_delivery_adapter,
)


class TestEmailSenders:
    @pytest.mark.asyncio
    async def test_sendgrid_provider_type(self):
        s = SendGridSender()
        assert s.provider_type() == "sendgrid"

    @pytest.mark.asyncio
    async def test_sendgrid_send_returns_expected(self):
        s = SendGridSender()
        result = await s.send(
            to=["a@b.com", "c@d.com"],
            subject="Test",
            body="Body",
            from_email="from@test.com",
        )
        assert result["provider"] == "sendgrid"
        assert result["sent_count"] == 2
        assert result["status"] == "sent"
        assert result["message_id"].startswith("sg_")

    @pytest.mark.asyncio
    async def test_ses_provider_type(self):
        s = SESEmailSender()
        assert s.provider_type() == "ses"

    @pytest.mark.asyncio
    async def test_ses_send(self):
        s = SESEmailSender()
        result = await s.send(to=["x@y.com"], subject="S", body="B", from_email="f@t.com")
        assert result["provider"] == "ses"
        assert result["sent_count"] == 1
        assert result["message_id"].startswith("ses_")

    @pytest.mark.asyncio
    async def test_smtp_provider_type(self):
        s = SMTPEmailSender()
        assert s.provider_type() == "smtp"

    @pytest.mark.asyncio
    async def test_smtp_send(self):
        s = SMTPEmailSender()
        result = await s.send(to=["x@y.com"], subject="S", body="B", from_email="f@t.com")
        assert result["provider"] == "smtp"
        assert result["message_id"].startswith("smtp_")

    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError):
            EmailSender()

    def test_registry_contains_all_three(self):
        assert set(SENDER_REGISTRY.keys()) == {"sendgrid", "ses", "smtp"}
        assert isinstance(SENDER_REGISTRY["sendgrid"], SendGridSender)
        assert isinstance(SENDER_REGISTRY["ses"], SESEmailSender)
        assert isinstance(SENDER_REGISTRY["smtp"], SMTPEmailSender)

    def test_get_sender_returns_correct_instance(self):
        assert isinstance(get_sender("sendgrid"), SendGridSender)
        assert isinstance(get_sender("ses"), SESEmailSender)
        assert isinstance(get_sender("smtp"), SMTPEmailSender)
        assert get_sender("unknown") is None


class TestNotificationDeliveryAdapters:
    @pytest.mark.asyncio
    async def test_base_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await NotificationDeliveryAdapter().deliver(uuid4(), "t", "b", "email")

    @pytest.mark.asyncio
    async def test_email_adapter_returns_true(self):
        assert await EmailNotificationAdapter().deliver(uuid4(), "t", "b", "email") is True

    @pytest.mark.asyncio
    async def test_sms_adapter_returns_true(self):
        assert await SMSNotificationAdapter().deliver(uuid4(), "t", "b", "sms") is True

    @pytest.mark.asyncio
    async def test_slack_adapter_returns_true(self):
        assert await SlackNotificationAdapter().deliver(uuid4(), "t", "b", "slack") is True

    def test_get_delivery_adapter_returns_correct(self):
        assert isinstance(get_delivery_adapter("email"), EmailNotificationAdapter)
        assert isinstance(get_delivery_adapter("sms"), SMSNotificationAdapter)
        assert isinstance(get_delivery_adapter("slack"), SlackNotificationAdapter)

    def test_unknown_channel_defaults_to_email(self):
        assert isinstance(get_delivery_adapter("carrier-pigeon"), EmailNotificationAdapter)


class TestPublishingAdapters:
    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError):
            PublishingAdapter()

    @pytest.mark.asyncio
    async def test_website_adapter_slugifies_title(self):
        content = Content(id=uuid4(), title="My Blog Post / About Things")
        adapter = WebsiteAdapter()
        url = await adapter.publish(content, metadata={"site_url": "https://mysite.com"})
        # / becomes -, spaces become -, so "My Blog Post / About Things" -> "my-blog-post---about-things"
        assert url == "https://mysite.com/blog/my-blog-post---about-things"

    @pytest.mark.asyncio
    async def test_website_adapter_uses_default_site_url(self):
        content = Content(id=uuid4(), title="Test")
        adapter = WebsiteAdapter()
        url = await adapter.publish(content)
        assert url == "https://example.com/blog/test"

    @pytest.mark.asyncio
    async def test_website_adapter_truncates_slug(self):
        long_title = "A" * 100
        content = Content(id=uuid4(), title=long_title)
        adapter = WebsiteAdapter()
        url = await adapter.publish(content)
        assert len(url.split("/")[-1]) == 80

    @pytest.mark.asyncio
    async def test_twitter_adapter_returns_tweet_url(self):
        content = Content(id=uuid4(), body="This is a tweet")
        adapter = TwitterAdapter()
        url = await adapter.publish(content)
        assert url.startswith("https://twitter.com/status/tweet_")
        assert "tweet_" in url

    @pytest.mark.asyncio
    async def test_twitter_adapter_truncates_body_280(self):
        content = Content(id=uuid4(), body="X" * 300)
        adapter = TwitterAdapter()
        url = await adapter.publish(content)
        assert url.startswith("https://twitter.com/status/tweet_")

    @pytest.mark.asyncio
    async def test_linkedin_adapter(self):
        content = Content(id=uuid4(), title="Post")
        adapter = LinkedInAdapter()
        url = await adapter.publish(content)
        assert url.startswith("https://linkedin.com/feed/update/post_")

    @pytest.mark.asyncio
    async def test_facebook_adapter(self):
        content = Content(id=uuid4())
        adapter = FacebookAdapter()
        url = await adapter.publish(content)
        assert url.startswith("https://facebook.com/fb_")

    @pytest.mark.asyncio
    async def test_instagram_adapter(self):
        content = Content(id=uuid4())
        adapter = InstagramAdapter()
        url = await adapter.publish(content)
        assert url.startswith("https://instagram.com/p/ig_")

    @pytest.mark.asyncio
    async def test_email_adapter(self):
        content = Content(id=uuid4())
        adapter = EmailAdapter()
        url = await adapter.publish(content)
        assert url.startswith("email://campaign/email_")

    def test_registry_contains_all(self):
        assert set(ADAPTER_REGISTRY.keys()) == {
            "website",
            "twitter",
            "linkedin",
            "facebook",
            "instagram",
            "email",
        }

    def test_get_adapter(self):
        assert isinstance(get_adapter("website"), WebsiteAdapter)
        assert isinstance(get_adapter("twitter"), TwitterAdapter)
        assert get_adapter("unknown") is None


class TestReportDeliveryAdapters:
    @pytest.mark.asyncio
    async def test_base_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await ReportDeliveryAdapter().deliver("r", "c", "f", "n")

    @pytest.mark.asyncio
    async def test_email_delivery(self, caplog):
        caplog.set_level("INFO")
        result = await ReportEmailDeliveryAdapter().deliver(
            "user@example.com", "content body", "csv", "Weekly Report"
        )
        assert result is True
        assert "Sending 'Weekly Report' (csv) to user@example.com" in caplog.text
        assert "Content preview:" in caplog.text

    @pytest.mark.asyncio
    async def test_slack_delivery_normalizes_channel(self, caplog):
        caplog.set_level("INFO")
        result = await ReportSlackDeliveryAdapter().deliver("alerts", "content", "json", "Alert")
        assert result is True
        assert "Posting 'Alert' to @alerts" in caplog.text

    @pytest.mark.asyncio
    async def test_slack_delivery_keeps_hash(self, caplog):
        caplog.set_level("INFO")
        await ReportSlackDeliveryAdapter().deliver("#general", "content", "json", "Alert")
        assert "Posting 'Alert' to #general" in caplog.text

    @pytest.mark.asyncio
    async def test_webhook_delivery(self, caplog):
        caplog.set_level("INFO")
        result = await WebhookDeliveryAdapter().deliver(
            "https://hook.site/abc", "content", "json", "Webhook"
        )
        assert result is True
        assert "POST 'Webhook' to https://hook.site/abc" in caplog.text

    def test_get_delivery_adapter_known(self):
        assert isinstance(get_report_delivery_adapter("email"), ReportEmailDeliveryAdapter)
        assert isinstance(get_report_delivery_adapter("slack"), ReportSlackDeliveryAdapter)
        assert isinstance(get_report_delivery_adapter("webhook"), WebhookDeliveryAdapter)

    def test_unknown_channel_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown delivery channel"):
            get_report_delivery_adapter("carrier-pigeon")
