from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.infrastructure.external_adapters.agents.tool_handlers import (
    create_campaign_handler,
    create_content_handler,
    list_campaigns_handler,
    register_tools,
)


class TestCreateCampaignHandler:
    async def test_success(self):
        db_session = MagicMock()
        campaign = MagicMock()
        campaign.name = "AI: Test Campaign"
        campaign.status = "draft"
        campaign.id = uuid4()

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=campaign)

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.CreateCampaignUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.CampaignRepositoryImpl"
            ):
                result = await create_campaign_handler(
                    db_session, organization_id=str(uuid4()), query="Test Campaign"
                )

        assert "Created campaign" in result["response"]
        assert "campaign_id" in result

    async def test_error(self):
        db_session = MagicMock()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Budget too low"))

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.CreateCampaignUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.CampaignRepositoryImpl"
            ):
                result = await create_campaign_handler(
                    db_session, organization_id=str(uuid4()), query="Test"
                )

        assert "error" in result
        assert "Budget too low" in result["error"]


class TestListCampaignsHandler:
    async def test_with_campaigns(self):
        db_session = MagicMock()
        c1 = MagicMock()
        c1.name = "Campaign 1"
        c1.status = "active"
        c2 = MagicMock()
        c2.name = "Campaign 2"
        c2.status = "draft"

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=[c1, c2])

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.ListCampaignsUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.CampaignRepositoryImpl"
            ):
                result = await list_campaigns_handler(db_session, organization_id=str(uuid4()))

        assert "2 campaigns" in result["response"]

    async def test_empty(self):
        db_session = MagicMock()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=[])

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.ListCampaignsUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.CampaignRepositoryImpl"
            ):
                result = await list_campaigns_handler(db_session, organization_id=str(uuid4()))

        assert "0 campaigns" in result["response"]


class TestCreateContentHandler:
    async def test_success(self):
        db_session = MagicMock()
        content = MagicMock()
        content.title = "AI: Test Content"
        content.status = "draft"
        content.id = uuid4()

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=content)

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.CreateContentUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.ContentRepositoryImpl"
            ):
                result = await create_content_handler(
                    db_session, organization_id=str(uuid4()), query="Test Content"
                )

        assert "Created content" in result["response"]
        assert "content_id" in result

    async def test_error(self):
        db_session = MagicMock()
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Title too long"))

        with patch(
            "app.infrastructure.external_adapters.agents.tool_handlers.CreateContentUseCase",
            return_value=mock_use_case,
        ):
            with patch(
                "app.infrastructure.external_adapters.agents.tool_handlers.ContentRepositoryImpl"
            ):
                result = await create_content_handler(
                    db_session, organization_id=str(uuid4()), query="Test"
                )

        assert "error" in result
        assert "Title too long" in result["error"]


class TestRegisterTools:
    def test_register_tools(self):
        registry = MagicMock()

        register_tools(registry, MagicMock())

        assert registry.register.call_count == 3
        calls = [c.args[0].name for c in registry.register.call_args_list]
        assert "create_campaign" in calls
        assert "list_campaigns" in calls
        assert "create_content" in calls
