"""Tests for Agent Governance Middleware — runtime enforcement of autonomy.

Tests the GovernanceMiddleware that intercepts agent tool calls and
checks them against autonomy config before execution.
"""

import pytest
from uuid import uuid4

from services.agent_orchestrator.governance import (
    GovernanceMiddleware,
    GovernanceCheckResult,
    TOOL_TO_ACTION_MAP,
    map_tool_to_action,
    create_governance_middleware,
)
from apps.api.app.domain.entities.governance.autonomy import (
    AutonomyConfig,
    AutonomyLevel,
)


ORG_ID = uuid4()


# ── Tool-to-Action Mapping Tests ───────────────────────────────────────


class TestToolActionMapping:
    def test_content_generate_mapped(self):
        assert map_tool_to_action("generate_content") == "content.generate"

    def test_campaign_launch_mapped(self):
        assert map_tool_to_action("launch_campaign") == "campaign.launch"

    def test_unknown_tool_defaults(self):
        assert map_tool_to_action("unknown_tool") == "unknown.action"

    def test_all_mapped_actions_are_valid_risk_actions(self):
        """Every mapped action should exist in the risk classification."""
        from apps.api.app.domain.entities.governance.autonomy import ACTION_RISK_LEVELS
        for tool_name, action_name in TOOL_TO_ACTION_MAP.items():
            assert action_name in ACTION_RISK_LEVELS or action_name == "unknown.action"


# ── GovernanceCheckResult Tests ────────────────────────────────────────


class TestGovernanceCheckResult:
    def test_to_dict(self):
        result = GovernanceCheckResult(
            allowed=True,
            action_name="content.generate",
            risk_level=1,
            autonomy_level=1,
        )
        d = result.to_dict()
        assert d["allowed"] is True
        assert d["action_name"] == "content.generate"
        assert d["risk_level"] == 1


# ── GovernanceMiddleware Tests ─────────────────────────────────────────


class TestGovernanceMiddlewareFullAuto:
    """Tests at FULL_AUTO autonomy level."""

    def _make_middleware(self) -> GovernanceMiddleware:
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.FULL_AUTO,
        )
        return GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="ContentSpecialist",
        )

    def test_generate_content_allowed(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("generate_content")
        assert result.allowed is True
        assert result.blocked is False

    def test_launch_campaign_allowed(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("launch_campaign")
        assert result.allowed is True

    def test_any_tool_allowed(self):
        mw = self._make_middleware()
        for tool in ["publish_content", "set_budget", "connect_account"]:
            result = mw.check_tool_call(tool)
            assert result.allowed is True

    def test_action_log_recorded(self):
        mw = self._make_middleware()
        mw.check_tool_call("generate_content")
        mw.check_tool_call("launch_campaign")
        log = mw.get_action_log()
        assert len(log) == 2
        assert log[0]["outcome"] == "allowed"

    def test_clear_log(self):
        mw = self._make_middleware()
        mw.check_tool_call("generate_content")
        mw.clear_action_log()
        assert len(mw.get_action_log()) == 0


class TestGovernanceMiddlewareSemiAuto:
    """Tests at SEMI_AUTO autonomy level."""

    def _make_middleware(self) -> GovernanceMiddleware:
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
            auto_approve_spend_limit=100.0,
        )
        return GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="AdvertisingDirector",
        )

    def test_low_risk_allowed(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("generate_content")
        assert result.allowed is True
        assert result.risk_level == 1

    def test_high_risk_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("launch_campaign")
        assert result.blocked is True
        assert result.requires_approval is True
        assert result.risk_level == 2

    def test_low_risk_under_spend_limit(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("update_bid", {"amount": 50})
        assert result.allowed is True

    def test_low_risk_over_spend_limit(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("update_bid", {"amount": 200})
        assert result.requires_approval is True
        assert result.allowed is False

    def test_pause_campaign_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("pause_campaign")
        assert result.blocked is True

    def test_publish_content_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("publish_content")
        assert result.blocked is True

    def test_analytics_report_allowed(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("generate_report")
        assert result.allowed is True


class TestGovernanceMiddlewareAdvisory:
    """Tests at ADVISORY autonomy level (default)."""

    def _make_middleware(self) -> GovernanceMiddleware:
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.ADVISORY,
        )
        return GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="ContentSpecialist",
        )

    def test_everything_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("generate_content")
        assert result.blocked is True
        assert result.requires_approval is True

    def test_analytics_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("query_analytics")
        assert result.blocked is True

    def test_unknown_tool_blocked(self):
        mw = self._make_middleware()
        result = mw.check_tool_call("unknown_tool")
        assert result.blocked is True


class TestGovernanceMiddlewareOverrides:
    """Tests with per-agent-type and per-action overrides."""

    def test_agent_type_override(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.ADVISORY,
        )
        config.set_agent_level("ContentSpecialist", AutonomyLevel.FULL_AUTO)
        mw = GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="ContentSpecialist",
        )
        result = mw.check_tool_call("generate_content")
        assert result.allowed is True

    def test_action_override_priority(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.FULL_AUTO,
        )
        config.action_overrides["campaign.launch"] = AutonomyLevel.ADVISORY
        mw = GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="AdvertisingDirector",
        )
        result = mw.check_tool_call("launch_campaign")
        assert result.blocked is True

    def test_custom_tool_action_map(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
        )
        custom_map = {"my_custom_tool": "content.generate"}
        mw = GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
            agent_type="ContentSpecialist",
            tool_action_map=custom_map,
        )
        result = mw.check_tool_call("my_custom_tool")
        assert result.allowed is True  # content.generate is low-risk

    def test_spend_from_budget_amount_param(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
            auto_approve_spend_limit=100.0,
        )
        mw = GovernanceMiddleware(
            organization_id=ORG_ID,
            autonomy_config=config,
        )
        result = mw.check_tool_call("update_bid", {"budget_amount": 200})
        assert result.requires_approval is True


# ── Factory Function Tests ─────────────────────────────────────────────


class TestCreateGovernanceMiddleware:
    def test_creates_with_defaults(self):
        mw = create_governance_middleware(ORG_ID)
        assert mw.organization_id == ORG_ID
        assert mw.autonomy_config.default_level == AutonomyLevel.ADVISORY

    def test_creates_with_custom_config(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.FULL_AUTO)
        mw = create_governance_middleware(ORG_ID, autonomy_config=config)
        assert mw.autonomy_config.default_level == AutonomyLevel.FULL_AUTO
