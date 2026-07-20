from uuid import uuid4

import pytest

from app.domain.entities.campaigns.campaign import Campaign
from app.domain.exceptions.domain_exceptions import ValidationError


class TestCampaignDomain:
    def test_create_valid_campaign(self):
        org_id = uuid4()
        user_id = uuid4()
        campaign = Campaign.create(
            organization_id=org_id,
            name="Summer Sale 2026",
            created_by=user_id,
            channels=["email", "social"],
            objective="conversion",
        )
        assert campaign.name == "Summer Sale 2026"
        assert campaign.status == "draft"
        assert campaign.organization_id == org_id
        assert campaign.channels == ["email", "social"]

    def test_create_campaign_empty_name_raises_error(self):
        with pytest.raises(ValidationError, match="Campaign name is required"):
            Campaign.create(organization_id=uuid4(), name="", created_by=uuid4())

    def test_create_campaign_invalid_channel_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid channels"):
            Campaign.create(
                organization_id=uuid4(),
                name="Test",
                created_by=uuid4(),
                channels=["invalid_channel"],
            )

    def test_status_transitions_from_draft(self):
        org_id = uuid4()
        campaign = Campaign.create(organization_id=org_id, name="Test", created_by=uuid4())
        assert campaign.status == "draft"

        campaign.transition_to("pending_approval")
        assert campaign.status == "pending_approval"

        campaign.transition_to("archived")
        assert campaign.status == "archived"

    def test_status_transition_invalid(self):
        campaign = Campaign.create(organization_id=uuid4(), name="Test", created_by=uuid4())
        with pytest.raises(ValidationError, match="Cannot transition"):
            campaign.transition_to("completed")

    def test_budget_validation(self):
        campaign = Campaign.create(organization_id=uuid4(), name="Test", created_by=uuid4())
        with pytest.raises(ValidationError, match="Budget must be positive"):
            campaign.update_budget(-100)

    def test_update_budget_success(self):
        campaign = Campaign.create(organization_id=uuid4(), name="Test", created_by=uuid4())
        campaign.update_budget(5000)
        assert campaign.budget_amount == 5000

    def test_dates_validation(self):
        with pytest.raises(ValidationError, match="Start date must be before end date"):
            from datetime import date

            Campaign.create(
                organization_id=uuid4(),
                name="Test",
                created_by=uuid4(),
                start_date=date(2026, 12, 31),
                end_date=date(2026, 1, 1),
            )
