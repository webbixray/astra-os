from uuid import uuid4

import pytest

from app.domain.entities.email.email_campaign import EMAIL_CAMPAIGN_STATUSES, EmailCampaign
from app.domain.entities.email.email_event import EMAIL_EVENT_TYPES, EmailEvent
from app.domain.entities.email.email_provider import EMAIL_PROVIDER_TYPES, EmailProvider
from app.domain.exceptions.domain_exceptions import ValidationError


class TestEmailCampaign:
    def test_create_valid_campaign(self):
        org_id = uuid4()
        prov_id = uuid4()
        user_id = uuid4()
        c = EmailCampaign.create(
            organization_id=org_id,
            provider_id=prov_id,
            name="Welcome Series",
            subject="Welcome!",
            body="Hello {{name}}",
            from_email="hello@example.com",
            created_by=user_id,
            from_name="Team",
        )
        assert c.organization_id == org_id
        assert c.provider_id == prov_id
        assert c.name == "Welcome Series"
        assert c.subject == "Welcome!"
        assert c.body == "Hello {{name}}"
        assert c.from_email == "hello@example.com"
        assert c.from_name == "Team"
        assert c.status == "draft"
        assert c.recipient_count == 0
        assert c.sent_count == 0

    def test_create_blank_name_raises(self):
        with pytest.raises(ValidationError, match="Campaign name is required"):
            EmailCampaign.create(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="",
                subject="X",
                body="X",
                from_email="x@x.com",
                created_by=uuid4(),
            )

    def test_create_blank_subject_raises(self):
        with pytest.raises(ValidationError, match="Subject is required"):
            EmailCampaign.create(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="X",
                subject="",
                body="X",
                from_email="x@x.com",
                created_by=uuid4(),
            )

    def test_create_blank_body_raises(self):
        with pytest.raises(ValidationError, match="Body is required"):
            EmailCampaign.create(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="X",
                subject="X",
                body="",
                from_email="x@x.com",
                created_by=uuid4(),
            )

    def test_create_invalid_from_email_raises(self):
        with pytest.raises(ValidationError, match="Valid from email is required"):
            EmailCampaign.create(
                organization_id=uuid4(),
                provider_id=uuid4(),
                name="X",
                subject="X",
                body="X",
                from_email="invalid-email",
                created_by=uuid4(),
            )

    def test_send_from_draft(self):
        c = EmailCampaign.create(
            organization_id=uuid4(),
            provider_id=uuid4(),
            name="X",
            subject="X",
            body="X",
            from_email="x@x.com",
            created_by=uuid4(),
        )
        c.send()
        assert c.status == "sending"

    def test_send_from_scheduled(self):
        c = EmailCampaign.create(
            organization_id=uuid4(),
            provider_id=uuid4(),
            name="X",
            subject="X",
            body="X",
            from_email="x@x.com",
            created_by=uuid4(),
        )
        c.status = "scheduled"
        c.send()
        assert c.status == "sending"

    def test_send_from_other_status_raises(self):
        c = EmailCampaign.create(
            organization_id=uuid4(),
            provider_id=uuid4(),
            name="X",
            subject="X",
            body="X",
            from_email="x@x.com",
            created_by=uuid4(),
        )
        c.status = "sent"
        with pytest.raises(ValidationError, match="Cannot send campaign in status"):
            c.send()

    def test_complete_sets_sent(self):
        c = EmailCampaign.create(
            organization_id=uuid4(),
            provider_id=uuid4(),
            name="X",
            subject="X",
            body="X",
            from_email="x@x.com",
            created_by=uuid4(),
        )
        c.complete(100)
        assert c.status == "sent"
        assert c.sent_count == 100
        assert c.sent_at is not None

    def test_fail_sets_failed(self):
        c = EmailCampaign.create(
            organization_id=uuid4(),
            provider_id=uuid4(),
            name="X",
            subject="X",
            body="X",
            from_email="x@x.com",
            created_by=uuid4(),
        )
        c.fail()
        assert c.status == "failed"


class TestEmailEvent:
    def test_create_event(self):
        camp_id = uuid4()
        e = EmailEvent.create(
            campaign_id=camp_id,
            event_type="opened",
            recipient_email="user@example.com",
            metadata={"browser": "Chrome"},
        )
        assert e.campaign_id == camp_id
        assert e.event_type == "opened"
        assert e.recipient_email == "user@example.com"
        assert e.metadata == {"browser": "Chrome"}

    def test_defaults(self):
        e = EmailEvent(campaign_id=uuid4())
        assert e.event_type == "sent"
        assert e.metadata == {}


class TestEmailProvider:
    def test_create_valid_provider(self):
        org_id = uuid4()
        user_id = uuid4()
        p = EmailProvider.create(
            organization_id=org_id,
            provider_type="sendgrid",
            name="My SendGrid",
            api_key="SG.xxx",
            from_email="no-reply@example.com",
            created_by=user_id,
            from_name="Team",
        )
        assert p.organization_id == org_id
        assert p.provider_type == "sendgrid"
        assert p.name == "My SendGrid"
        assert p.api_key == "SG.xxx"
        assert p.from_email == "no-reply@example.com"
        assert p.is_verified is False
        assert p.is_active is True

    def test_invalid_provider_type_raises(self):
        with pytest.raises(ValidationError, match="Invalid provider type"):
            EmailProvider.create(
                organization_id=uuid4(),
                provider_type="mailgun",
                name="X",
                api_key="X",
                from_email="x@x.com",
                created_by=uuid4(),
            )

    def test_missing_api_key_raises(self):
        with pytest.raises(ValidationError, match="API key is required"):
            EmailProvider.create(
                organization_id=uuid4(),
                provider_type="sendgrid",
                name="X",
                api_key="",
                from_email="x@x.com",
                created_by=uuid4(),
            )

    def test_invalid_from_email_raises(self):
        with pytest.raises(ValidationError, match="Valid from email is required"):
            EmailProvider.create(
                organization_id=uuid4(),
                provider_type="sendgrid",
                name="X",
                api_key="X",
                from_email="not-an-email",
                created_by=uuid4(),
            )


class TestEmailConstants:
    def test_campaign_statuses(self):
        assert EMAIL_CAMPAIGN_STATUSES == [
            "draft",
            "scheduled",
            "sending",
            "sent",
            "partially_sent",
            "failed",
        ]

    def test_event_types(self):
        assert "sent" in EMAIL_EVENT_TYPES
        assert "opened" in EMAIL_EVENT_TYPES
        assert "clicked" in EMAIL_EVENT_TYPES
        assert "bounced" in EMAIL_EVENT_TYPES
        assert "complained" in EMAIL_EVENT_TYPES
        assert "unsubscribed" in EMAIL_EVENT_TYPES

    def test_provider_types(self):
        assert EMAIL_PROVIDER_TYPES == ["sendgrid", "ses", "smtp"]
