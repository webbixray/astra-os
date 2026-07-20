from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.presentation.middleware.feature_flags import (
    FEATURE_PRESETS,
    FeatureGate,
    get_plan_features,
    require_feature,
)


class TestGetPlanFeatures:
    def test_free_plan(self) -> None:
        features = get_plan_features("free")
        assert "basic_analytics" in features
        assert "content_management" in features
        assert "ai_content_generation" not in features
        assert "advertising_integration" not in features

    def test_professional_plan(self) -> None:
        features = get_plan_features("professional")
        assert "advertising_integration" in features
        assert "workflow_automation" in features
        assert "ai_content_generation" not in features

    def test_business_plan(self) -> None:
        features = get_plan_features("business")
        assert "ai_content_generation" in features
        assert "advertising_integration" in features
        assert "workflow_automation" in features

    def test_enterprise_plan(self) -> None:
        features = get_plan_features("enterprise")
        assert "white_label" in features
        assert "saml_sso" in features
        assert "dedicated_infrastructure" in features
        assert "audit_logs" in features

    def test_unknown_plan_defaults_to_free(self) -> None:
        features = get_plan_features("nonexistent")
        assert features == set(FEATURE_PRESETS["free"])

    def test_business_superset_of_professional(self) -> None:
        professional = get_plan_features("professional")
        business = get_plan_features("business")
        assert professional <= business

    def test_enterprise_superset_of_business(self) -> None:
        business = get_plan_features("business")
        enterprise = get_plan_features("enterprise")
        assert business <= enterprise


class TestRequireFeature:
    @pytest.fixture
    def org_id(self) -> str:
        return uuid4()

    async def test_allows_feature_on_plan(self, org_id: str) -> None:
        result = await require_feature("basic_analytics", org_id, "free")
        assert result is True

    async def test_denies_feature_not_on_plan(self, org_id: str) -> None:
        with patch(
            "app.infrastructure.db.repositories.feature_flag_repository.FeatureFlagRepository.find_by_key",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await require_feature("ai_content_generation", org_id, "free", AsyncMock())
            assert exc_info.value.status_code == 403

    async def test_allows_override(self, org_id: str) -> None:
        with (
            patch(
                "app.presentation.middleware.feature_flags.get_plan_features",
                return_value=set(),
            ),
            patch(
                "app.infrastructure.db.repositories.feature_flag_repository.FeatureFlagRepository.find_by_key",
                new=AsyncMock(return_value=MagicMock(is_enabled=True)),
            ),
        ):
            result = await require_feature("ai_content_generation", org_id, "free", AsyncMock())
            assert result is True

    async def test_override_disabled_still_denies(self, org_id: str) -> None:
        with (
            patch(
                "app.presentation.middleware.feature_flags.get_plan_features",
                return_value=set(),
            ),
            patch(
                "app.infrastructure.db.repositories.feature_flag_repository.FeatureFlagRepository.find_by_key",
                new=AsyncMock(return_value=MagicMock(is_enabled=False)),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await require_feature("ai_content_generation", org_id, "free", AsyncMock())
            assert exc_info.value.status_code == 403

    async def test_feature_gate_class(self, org_id: str) -> None:
        gate = FeatureGate("advertising_integration")

        with patch(
            "app.presentation.middleware.feature_flags.require_feature",
            new=AsyncMock(return_value=True),
        ):
            result = await gate(org_id, "professional", AsyncMock())
            assert result is None


class TestPlanFeaturePresets:
    def test_advertising_on_professional(self) -> None:
        assert "advertising_integration" in get_plan_features("professional")

    def test_advertising_not_on_starter(self) -> None:
        assert "advertising_integration" not in get_plan_features("starter")

    def test_ai_content_on_business(self) -> None:
        assert "ai_content_generation" in get_plan_features("business")

    def test_ai_content_not_on_professional(self) -> None:
        assert "ai_content_generation" not in get_plan_features("professional")

    def test_email_on_starter(self) -> None:
        assert "email_marketing" in get_plan_features("starter")

    def test_workflow_on_professional(self) -> None:
        assert "workflow_automation" in get_plan_features("professional")

    def test_workflow_not_on_starter(self) -> None:
        assert "workflow_automation" not in get_plan_features("starter")

    def test_advanced_reports_on_professional(self) -> None:
        assert "custom_reports" in get_plan_features("professional")

    def test_advanced_reports_not_on_starter(self) -> None:
        assert "custom_reports" not in get_plan_features("starter")
