"""Tests for campaign routes API endpoints."""

import hashlib
"""Tests for campaign routes API endpoints."""

import hashlib
import hmac
import secrets
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.entities.advertising.ad_campaign import AdCampaign, CampaignObjective, SyncStatus
from app.domain.entities.campaigns.ab_test import ABTest, ABTestVariant
from app.domain.entities.campaigns.campaign_budget import CampaignBudget
from app.domain.entities.campaigns.campaign_template import CampaignTemplate
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.main import create_app
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.routes.campaigns.campaign_routes import (
    get_create_use_case,
    get_get_use_case,
    get_list_use_case,
    get_update_use_case,
    get_budget_repo,
    get_set_budget_uc,
    get_get_budget_uc,
    get_record_spend_uc,
    get_template_repo,
    get_create_template_uc,
    get_list_templates_uc,
    get_get_template_uc,
    get_delete_template_uc,
    get_clone_uc,
    get_abtest_repo,
    get_create_abtest_uc,
    get_list_abtests_uc,
    get_get_abtest_uc,
    get_add_variant_uc,
    get_start_abtest_uc,
    get_determine_winner_uc,
    get_record_metrics_uc,
)


def _mock_campaign(**kwargs):
    """Create a mock campaign."""
    c = MagicMock(spec=AdCampaign)
    c.id = kwargs.get("id", uuid4())
    c.organization_id = kwargs.get("organization_id", uuid4())
    c.name = kwargs.get("name", "Test Campaign")
    c.description = kwargs.get("description", "Test Description")
    c.status = kwargs.get("status", "draft")
    c.budget_amount = kwargs.get("budget_amount", 1000.0)
    c.budget_currency = kwargs.get("budget_currency", "USD")
    c.start_date = kwargs.get("start_date", datetime.now())
    c.end_date = kwargs.get("end_date", None)
    c.channels = kwargs.get("channels", ["meta", "google"])
    c.objective = kwargs.get("objective", "conversions")
    c.created_by = kwargs.get("created_by", uuid4())
    c.ai_generated = kwargs.get("ai_generated", False)
    c.created_at = kwargs.get("created_at", datetime.now())
    c.updated_at = kwargs.get("updated_at", datetime.now())
    return c


def _mock_budget(**kwargs):
    """Create a mock campaign budget."""
    b = MagicMock()
    b.id = kwargs.get("id", uuid4())
    b.campaign_id = kwargs.get("campaign_id", uuid4())
    b.total_budget = kwargs.get("total_budget", 10000.0)
    b.currency = kwargs.get("currency", "USD")
    b.alert_threshold = kwargs.get("alert_threshold", 80.0)
    b.period_start = kwargs.get("period_start", datetime.now())
    b.period_end = kwargs.get("period_end", None)
    b.spent = kwargs.get("spent", 0.0)
    b.remaining = kwargs.get("total_budget", 10000.0) - kwargs.get("spent", 0.0)
    b.spend_pct = (kwargs.get("spent", 0.0) / kwargs.get("total_budget", 10000.0)) * 100.0 if kwargs.get("total_budget", 10000.0) > 0 else 0.0
    b.is_alert_triggered = b.spend_pct >= kwargs.get("alert_threshold", 80.0)
    return b


def _mock_template(**kwargs):
    """Create a mock campaign template."""
    t = MagicMock()
    t.id = kwargs.get("id", uuid4())
    t.organization_id = kwargs.get("organization_id", uuid4())
    t.name = kwargs.get("name", "Test Template")
    t.description = kwargs.get("description", "Test Template Description")
    t.channels = kwargs.get("channels", ["meta"])
    t.objective = kwargs.get("objective", "conversions")
    t.budget_amount = kwargs.get("budget_amount", 5000.0)
    t.budget_currency = kwargs.get("budget_currency", "USD")
    t.default_duration_days = kwargs.get("default_duration_days", 30)
    t.config = kwargs.get("config", {})
    t.created_at = kwargs.get("created_at", datetime.now())
    t.updated_at = kwargs.get("updated_at", datetime.now())
    return t


def _mock_abtest(**kwargs):
    """Create a mock A/B test."""
    a = MagicMock()
    a.id = kwargs.get("id", uuid4())
    a.campaign_id = kwargs.get("campaign_id", uuid4())
    a.name = kwargs.get("name", "Test A/B Test")
    a.description = kwargs.get("description", "")
    a.goal_metric = kwargs.get("goal_metric", "conversion_rate")
    a.status = kwargs.get("status", "draft")
    a.winner_variant_id = kwargs.get("winner_variant_id", None)
    a.created_at = kwargs.get("created_at", datetime.now())
    return a


def _mock_variant(**kwargs):
    """Create a mock A/B test variant."""
    v = MagicMock()
    v.id = kwargs.get("id", uuid4())
    v.ab_test_id = kwargs.get("ab_test_id", uuid4())
    v.name = kwargs.get("name", "Variant A")
    v.description = kwargs.get("description", "")
    v.config = kwargs.get("config", {})
    v.traffic_percent = kwargs.get("traffic_percent", 50.0)
    return v


@pytest.fixture
def app_fixture() -> FastAPI:
    """Create test app with mocked dependencies."""
    with patch("app.presentation.routes.campaigns.campaign_routes.campaigns_created", MagicMock()):
        a = create_app()

        # Mock DB session
        mock_member = MagicMock()
        mock_member.role = "owner"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_member)

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        async def mock_get_db():
            yield mock_session

        a.dependency_overrides[get_db] = mock_get_db

        # Fixed user ID for auth
        fixed_user_id = uuid4()
        a.dependency_overrides[require_user_id] = lambda: fixed_user_id
        a.dependency_overrides[require_org_role] = lambda *args, **kwargs: None

        yield a
        a.dependency_overrides.clear()


@pytest.fixture
def app(app_fixture) -> FastAPI:
    """Alias for app_fixture to maintain backward compatibility."""
    return app_fixture


@pytest.fixture
async def test_client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ============================================================
# CAMPAIGN CRUD TESTS
# ============================================================

class TestCampaignCreate:
    @pytest.mark.asyncio
    async def test_create_campaign_success(self, app: FastAPI, test_client: AsyncClient):
        # Get the fixed user_id from the app's dependency overrides
        user_id = app.dependency_overrides.get(require_user_id)
        if callable(user_id):
            user_id = user_id()
        
        mock_campaign = _mock_campaign(
            name="New Campaign",
            organization_id=uuid4(),
            created_by=user_id
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_campaign)
        app.dependency_overrides[get_create_use_case] = lambda: mock_use_case

        org_id = uuid4()
        
        # Setup CSRF
        from app.config import config
        secret = config.secret_key
        session_id = secrets.token_urlsafe(16)
        import time
        timestamp = int(time.time())
        msg = f"{session_id}:{timestamp}"
        signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
        csrf_token = f"{timestamp}:{signature}"
        test_client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
        csrf_headers = {"X-CSRF-Token": csrf_token}

        response = await test_client.post(
            "/api/v1/campaigns",
            json={
                "name": "New Campaign",
                "description": "Test campaign",
                "budget_amount": 5000.0,
                "budget_currency": "USD",
                "channels": ["meta", "google"],
                "objective": "conversions",
                "organization_id": str(org_id),
            },
            headers=csrf_headers,
        )

        assert response.status_code == 201
        data = response.json()
        print(f"Response data: {data}")  # Debug
        assert data["data"]["name"] == "New Campaign"
        assert data["data"]["status"] == "draft"
        assert data["data"]["budget_amount"] == 1000.0  # Mock returns default value

    @pytest.mark.asyncio
    async def test_create_campaign_validation_error(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=ValidationError("Invalid budget amount")
        )
        app.dependency_overrides[get_create_use_case] = lambda: mock_use_case

        org_id = uuid4()
        response = await test_client.post(
            "/api/v1/campaigns",
            json={
                "name": "New Campaign",
                "budget_amount": -100,  # Invalid
                "organization_id": str(org_id),
            },
        )

        assert response.status_code == 422
        assert "Invalid budget amount" in response.json()["detail"]


class TestCampaignGet:
    @pytest.mark.asyncio
    async def test_get_campaign_success(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        org_id = uuid4()
        mock_campaign = _mock_campaign(id=campaign_id, organization_id=org_id)

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_campaign)
        app.dependency_overrides[get_get_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/campaigns/{campaign_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(campaign_id)
        assert data["name"] == mock_campaign.name

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, app: FastAPI, test_client: AsyncClient):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("AdCampaign", str(uuid4()))
        )
        app.dependency_overrides[get_get_use_case] = lambda: mock_use_case

        response = await test_client.get(f"/api/v1/campaigns/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCampaignList:
    @pytest.mark.asyncio
    async def test_list_campaigns_success(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_campaigns = [
            _mock_campaign(id=uuid4(), organization_id=org_id, name=f"Campaign {i}")
            for i in range(3)
        ]

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_campaigns)
        app.dependency_overrides[get_list_use_case] = lambda: mock_use_case

        response = await test_client.get(
            f"/api/v1/campaigns?organization_id={org_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_campaigns_with_status_filter(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_campaigns = [
            _mock_campaign(id=uuid4(), organization_id=org_id, status=CampaignStatus.ACTIVE)
        ]

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_campaigns)
        app.dependency_overrides[get_list_use_case] = lambda: mock_use_case

        response = await test_client.get(
            f"/api/v1/campaigns?organization_id={org_id}&status=active"
        )

        assert response.status_code == 200
        mock_use_case.execute.assert_called_once_with(org_id=org_id, status="active")


class TestCampaignUpdate:
    @pytest.mark.asyncio
    async def test_update_campaign_success(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        org_id = uuid4()
        existing = _mock_campaign(id=campaign_id, organization_id=org_id)
        updated = _mock_campaign(
            id=campaign_id,
            organization_id=org_id,
            name="Updated Campaign",
            description="Updated description",
        )

        mock_get_use_case = MagicMock()
        mock_get_use_case.execute = AsyncMock(return_value=existing)

        mock_update_use_case = MagicMock()
        mock_update_use_case.execute = AsyncMock(return_value=updated)

        app.dependency_overrides[get_get_use_case] = lambda: mock_get_use_case
        app.dependency_overrides[get_update_use_case] = lambda: mock_update_use_case

        response = await test_client.patch(
            f"/api/v1/campaigns/{campaign_id}",
            json={"name": "Updated Campaign", "description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign"

    @pytest.mark.asyncio
    async def test_update_campaign_not_found(self, app: FastAPI, test_client: AsyncClient):
        mock_get_use_case = MagicMock()
        mock_get_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("AdCampaign", str(uuid4()))
        )
        app.dependency_overrides[get_get_use_case] = lambda: mock_get_use_case

        response = await test_client.patch(
            f"/api/v1/campaigns/{uuid4()}",
            json={"name": "Updated"},
        )

        assert response.status_code == 404


# ============================================================
# CAMPAIGN LIFECYCLE TESTS
# ============================================================

class TestCampaignLifecycle:
    @pytest.mark.asyncio
    async def test_launch_campaign_success(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        org_id = uuid4()
        mock_campaign = _mock_campaign(
            id=campaign_id,
            organization_id=org_id,
            status=CampaignStatus.ACTIVE,
        )

        # The launch endpoint creates its own repo/use_case, so we need to patch at module level
        with patch("app.presentation.routes.campaigns.campaign_routes.CampaignRepositoryImpl") as mock_repo_class, \
             patch("app.presentation.routes.campaigns.campaign_routes.LaunchCampaignUseCase") as mock_uc_class:

            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_campaign)
            mock_repo_class.return_value = mock_repo

            mock_uc = AsyncMock()
            mock_uc.execute = AsyncMock(return_value=mock_campaign)
            mock_uc_class.return_value = mock_uc

            response = await test_client.post(f"/api/v1/campaigns/{campaign_id}/launch")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_launch_campaign_not_found(self, app: FastAPI, test_client: AsyncClient):
        with patch("app.presentation.routes.campaigns.campaign_routes.CampaignRepositoryImpl") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = await test_client.post(f"/api/v1/campaigns/{uuid4()}/launch")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pause_campaign_success(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        org_id = uuid4()
        mock_campaign = _mock_campaign(
            id=campaign_id,
            organization_id=org_id,
            status=CampaignStatus.PAUSED,
        )

        with patch("app.presentation.routes.campaigns.campaign_routes.CampaignRepositoryImpl") as mock_repo_class, \
             patch("app.presentation.routes.campaigns.campaign_routes.PauseCampaignUseCase") as mock_uc_class:

            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_campaign)
            mock_repo_class.return_value = mock_repo

            mock_uc = AsyncMock()
            mock_uc.execute = AsyncMock(return_value=mock_campaign)
            mock_uc_class.return_value = mock_uc

            response = await test_client.post(f"/api/v1/campaigns/{campaign_id}/pause")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "paused"


# ============================================================
# BUDGET MANAGEMENT TESTS
# ============================================================

class TestCampaignBudget:
    @pytest.mark.asyncio
    async def test_set_campaign_budget(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        mock_budget = _mock_budget(campaign_id=campaign_id, total_budget=10000.0)

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_budget)
        app.dependency_overrides[get_set_budget_uc] = lambda: mock_uc

        response = await test_client.post(
            f"/api/v1/campaigns/{campaign_id}/budget",
            json={
                "total_budget": 10000.0,
                "currency": "USD",
                "alert_threshold": 80.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_budget"] == 10000.0

    @pytest.mark.asyncio
    async def test_get_campaign_budget(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        mock_budget = _mock_budget(campaign_id=campaign_id, total_budget=10000.0, spent=2500.0)

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_budget)
        app.dependency_overrides[get_get_budget_uc] = lambda: mock_uc

        response = await test_client.get(f"/api/v1/campaigns/{campaign_id}/budget")

        assert response.status_code == 200
        data = response.json()
        assert data["total_budget"] == 10000.0
        assert data["spent"] == 2500.0
        assert data["remaining"] == 7500.0

    @pytest.mark.asyncio
    async def test_record_spend(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        mock_budget = _mock_budget(campaign_id=campaign_id, total_budget=10000.0, spent=3000.0)

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_budget)
        app.dependency_overrides[get_record_spend_uc] = lambda: mock_uc

        response = await test_client.post(
            f"/api/v1/campaigns/{campaign_id}/spend",
            json={"amount": 500.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spent"] == 3000.0


# ============================================================
# TEMPLATE TESTS
# ============================================================

class TestCampaignTemplates:
    @pytest.mark.asyncio
    async def test_create_template(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_template = _mock_template(
            id=uuid4(),
            organization_id=org_id,
            name="Summer Campaign Template",
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_template)
        app.dependency_overrides[get_create_template_uc] = lambda: mock_uc

        response = await test_client.post(
            "/api/v1/campaigns/templates",
            json={
                "name": "Summer Campaign Template",
                "description": "Template for summer campaigns",
                "channels": ["meta", "google"],
                "objective": "conversions",
                "budget_amount": 5000.0,
                "budget_currency": "USD",
                "default_duration_days": 30,
                "config": {"daily_budget_cap": 200},
                "organization_id": str(org_id),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Summer Campaign Template"

    @pytest.mark.asyncio
    async def test_list_templates(self, app: FastAPI, test_client: AsyncClient):
        org_id = uuid4()
        mock_templates = [
            _mock_template(id=uuid4(), organization_id=org_id, name=f"Template {i}")
            for i in range(2)
        ]

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_templates)
        app.dependency_overrides[get_list_templates_uc] = lambda: mock_uc

        response = await test_client.get(f"/api/v1/campaigns/templates?organization_id={org_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_template(self, app: FastAPI, test_client: AsyncClient):
        template_id = uuid4()
        org_id = uuid4()
        mock_template = _mock_template(id=template_id, organization_id=org_id)

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_template)
        app.dependency_overrides[get_get_template_uc] = lambda: mock_uc

        response = await test_client.get(f"/api/v1/campaigns/templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(template_id)

    @pytest.mark.asyncio
    async def test_delete_template(self, app: FastAPI, test_client: AsyncClient):
        template_id = uuid4()

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock()
        app.dependency_overrides[get_delete_template_uc] = lambda: mock_uc

        response = await test_client.delete(f"/api/v1/campaigns/templates/{template_id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_clone_from_template(self, app: FastAPI, test_client: AsyncClient):
        template_id = uuid4()
        org_id = uuid4()
        mock_campaign = _mock_campaign(
            id=uuid4(),
            organization_id=org_id,
            name="Cloned Campaign",
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_campaign)
        app.dependency_overrides[get_clone_uc] = lambda: mock_uc

        response = await test_client.post(
            "/api/v1/campaigns/templates/clone",
            json={
                "template_id": str(template_id),
                "organization_id": str(org_id),
                "name": "Cloned Campaign",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Cloned Campaign"


# ============================================================
# A/B TEST TESTS
# ============================================================

class TestABTests:
    @pytest.mark.asyncio
    async def test_create_ab_test(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        mock_abtest = _mock_abtest(
            id=uuid4(),
            campaign_id=campaign_id,
            name="Test A/B",
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_abtest)
        app.dependency_overrides[get_create_abtest_uc] = lambda: mock_uc

        response = await test_client.post(
            "/api/v1/campaigns/ab-tests",
            json={
                "campaign_id": str(campaign_id),
                "name": "Test A/B",
                "goal_metric": "conversion_rate",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test A/B"

    @pytest.mark.asyncio
    async def test_list_ab_tests(self, app: FastAPI, test_client: AsyncClient):
        campaign_id = uuid4()
        mock_tests = [
            _mock_abtest(id=uuid4(), campaign_id=campaign_id, name=f"Test {i}")
            for i in range(2)
        ]

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_tests)
        app.dependency_overrides[get_list_abtests_uc] = lambda: mock_uc

        response = await test_client.get(f"/api/v1/campaigns/ab-tests?campaign_id={campaign_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_add_variant(self, app: FastAPI, test_client: AsyncClient):
        abtest_id = uuid4()
        mock_variant = _mock_variant(
            id=uuid4(),
            ab_test_id=abtest_id,
            name="Variant B",
            traffic_percent=50.0,
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_variant)
        app.dependency_overrides[get_add_variant_uc] = lambda: mock_uc

        response = await test_client.post(
            f"/api/v1/campaigns/ab-tests/{abtest_id}/variants",
            json={
                "name": "Variant B",
                "traffic_percent": 50.0,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Variant B"

    @pytest.mark.asyncio
    async def test_start_ab_test(self, app: FastAPI, test_client: AsyncClient):
        abtest_id = uuid4()
        mock_abtest = _mock_abtest(id=abtest_id, status="running")

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_abtest)
        app.dependency_overrides[get_start_abtest_uc] = lambda: mock_uc

        response = await test_client.post(f"/api/v1/campaigns/ab-tests/{abtest_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_record_variant_metrics(self, app: FastAPI, test_client: AsyncClient):
        abtest_id = uuid4()
        mock_variant = _mock_variant(
            id=uuid4(),
            ab_test_id=abtest_id,
            name="Variant A",
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_variant)
        app.dependency_overrides[get_record_metrics_uc] = lambda: mock_uc

        response = await test_client.post(
            f"/api/v1/campaigns/ab-tests/{abtest_id}/variants/Variant A/metrics",
            json={
                "impressions": 10000,
                "clicks": 500,
                "conversions": 50,
                "spend": 250.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["impressions"] == 10000

    @pytest.mark.asyncio
    async def test_determine_winner(self, app: FastAPI, test_client: AsyncClient):
        abtest_id = uuid4()
        mock_abtest = _mock_abtest(
            id=abtest_id,
            status="completed",
            winner_variant_id=uuid4(),
        )

        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(return_value=mock_abtest)
        app.dependency_overrides[get_determine_winner_uc] = lambda: mock_uc

        response = await test_client.post(
            f"/api/v1/campaigns/ab-tests/{abtest_id}/determine-winner"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"