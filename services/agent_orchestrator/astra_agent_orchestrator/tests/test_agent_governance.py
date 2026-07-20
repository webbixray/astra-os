"""Tests for Agent Governance Middleware — runtime enforcement of autonomy.

Tests the GovernanceMiddleware that intercepts agent tool calls and
checks them against autonomy config before execution.
"""

from uuid import uuid4

import pytest
from apps.api.app.domain.entities.governance.autonomy import (
    AutonomyConfig,
    AutonomyLevel,
)

from astra_agent_orchestrator.governance import (
    TOOL_TO_ACTION_MAP,
    GovernanceCheckResult,
    GovernanceMiddleware,
    create_governance_middleware,
    map_tool_to_action,
)

ORG_ID = uuid4()


# ── Tool-to-Action Mapping Tests ───────────────────────────────────────


class TestToolActionMapping:
    def test_content_generate_mapped(self):
        assert map_tool_to_action("generate_content") == "content.generate"

    def test_campaign_launch_mapped(self):
        assert map_tool_to_action("launch_campaign") == "campaign.launch"

    def test_unknown_tool_mapped(self):
        assert map_tool_to_action("unknown_tool") == "unknown.action"

    def test_all_known_tools_mapped(self):
        """Ensure all expected tools have mappings."""
        expected_mappings = {
            "generate_content": "content.generate",
            "generate_blog_post": "content.generate",
            "generate_social_post": "content.generate",
            "review_content": "content.review",
            "publish_content": "content.publish",
            "delete_content": "content.delete",
            "create_campaign": "campaign.create",
            "update_campaign": "campaign.update",
            "launch_campaign": "campaign.launch",
            "pause_campaign": "campaign.pause",
            "complete_campaign": "campaign.complete",
            "set_budget": "spend.allocate",
            "increase_budget": "spend.increase",
            "reallocate_budget": "budget.reallocate",
            "analyze_competitors": "research.competitors",
            "analyze_trends": "research.trends",
            "research_market": "research.analyze",
            "create_creative": "creative.create",
            "update_creative": "creative.update",
            "approve_creative": "creative.approve",
        }
        for tool, action in expected_mappings.items():
            assert map_tool_to_action(tool) == action, f"{tool} not mapped correctly"

    def test_action_map_completeness(self):
        """Ensure all mapped actions exist in risk classification."""
        from astra_agent_orchestrator.governance import get_action_risk_level

        for tool, action in TOOL_TO_ACTION_MAP.items():
            risk = get_action_risk_level(action)
            assert risk in (0, 1, 2), f"Action {action} has invalid risk level {risk}"


# ── GovernanceCheckResult Tests ────────────────────────────────────────


class TestGovernanceCheckResult:
    def test_allowed_result(self):

        result = GovernanceCheckResult(
            action_name="content.generate",
            risk_level=1,
            autonomy_level=1,
        )
        result.allowed = True
        result.reason = "SEMI_AUTO: low-risk auto-executed"

        assert result.allowed is True
        assert result.blocked is False
        assert result.requires_approval is False
        assert result.action_name == "content.generate"
        assert result.risk_level == 1

    def test_blocked_result(self):

        result = GovernanceCheckResult(
            action_name="campaign.launch",
            risk_level=2,
            autonomy_level=1,
        )
        result.blocked = True
        result.requires_approval = True
        result.reason = "High-risk tool requires approval"

        assert result.allowed is False
        assert result.blocked is True
        assert result.requires_approval is True

    def test_approval_needed_result(self):

        result = GovernanceCheckResult(
            action_name="spend.allocate",
            risk_level=1,
            autonomy_level=1,
        )
        result.requires_approval = True
        result.reason = "Spend exceeds auto-approve limit"

        assert result.allowed is False
        assert result.blocked is False
        assert result.requires_approval is True


# ── GovernanceMiddleware Tests ─────────────────────────────────────────


class TestGovernanceMiddleware:
    @pytest.fixture
    def middleware(self):
        return GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
                auto_approve_spend_limit=100.0,
            ),
            agent_type="CONTENT_SPECIALIST",
        )

    def test_full_auto_allows_everything(self):
        """FULL_AUTO should allow all actions regardless of risk."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.FULL_AUTO,
            ),
        )

        result = middleware.check_tool_call("launch_campaign", {"amount": 10000})
        assert result.allowed is True
        assert result.reason.startswith("FULL_AUTO")

        result = middleware.check_tool_call("spend.allocate", {"amount": 1000000})
        assert result.allowed is True

    def test_semi_auto_allows_low_risk(self):
        """SEMI_AUTO should allow low-risk actions."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
                auto_approve_spend_limit=100.0,
            ),
        )

        result = middleware.check_tool_call("generate_content", {})
        assert result.allowed is True
        assert "SEMI_AUTO" in result.reason

    def test_semi_auto_blocks_high_risk(self):
        """SEMI_AUTO should block high-risk actions."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
            ),
        )

        result = middleware.check_tool_call("launch_campaign", {})
        assert result.blocked is True
        assert result.requires_approval is True
        assert "high-risk" in result.reason.lower()

    def test_semi_auto_blocks_over_spend_limit(self):
        """SEMI_AUTO should block actions exceeding spend limit."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
                auto_approve_spend_limit=100.0,
            ),
        )

        result = middleware.check_tool_call("set_budget", {"amount": 200.0})
        assert result.requires_approval is True
        assert "exceeds auto-approve limit" in result.reason

    def test_advisory_blocks_everything(self):
        """ADVISORY should require approval for everything."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.ADVISORY,
            ),
        )

        result = middleware.check_tool_call("generate_content", {})
        assert result.blocked is True
        assert result.requires_approval is True
        assert "ADVISORY" in result.reason

    def test_agent_type_override(self):
        """Agent-type-specific autonomy level should override default."""
        config = AutonomyConfig.create(
            organization_id=uuid4(),
            default_level=AutonomyLevel.ADVISORY,
        )
        config.agent_levels["CONTENT_SPECIALIST"] = AutonomyLevel.SEMI_AUTO

        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=config,
            agent_type="CONTENT_SPECIALIST",
        )

        # CONTENT_SPECIALIST has SEMI_AUTO override
        result = middleware.check_tool_call("generate_content", {})
        assert result.allowed is True

    def test_action_override(self):
        """Action-specific override should take precedence."""
        config = AutonomyConfig.create(
            organization_id=uuid4(),
            default_level=AutonomyLevel.ADVISORY,
        )
        config.action_overrides["content.generate"] = AutonomyLevel.FULL_AUTO

        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=config,
        )

        result = middleware.check_tool_call("generate_content", {})
        assert result.allowed is True

    def test_spend_limit_enforcement(self):
        """Spend limits should be enforced at SEMI_AUTO."""
        config = AutonomyConfig.create(
            organization_id=uuid4(),
            default_level=AutonomyLevel.SEMI_AUTO,
            auto_approve_spend_limit=50.0,
        )

        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=config,
        )

        # Under limit - allowed
        result = middleware.check_tool_call("set_budget", {"amount": 30.0})
        assert result.allowed is True

        # Over limit - requires approval
        result = middleware.check_tool_call("set_budget", {"amount": 100.0})
        assert result.requires_approval is True

    def test_action_logging(self):
        """Governance decisions should be logged for auditing."""
        middleware = GovernanceMiddleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
            ),
            agent_type="CONTENT_SPECIALIST",
            agent_id="agent-123",
        )

        middleware.check_tool_call("generate_content", {})
        # launch_campaign with amount=1000 exceeds default spend limit of 100
        middleware.check_tool_call("launch_campaign", {"amount": 1000})

        log = middleware.get_action_log()
        assert len(log) == 2

        # First call - allowed (low risk, under spend limit)
        assert log[0]["action_name"] == "content.generate"
        assert log[0]["outcome"] == "allowed"
        assert log[0]["reason_category"] == "semi_auto_low_risk"

        # Second call - requires approval (over spend limit)
        assert log[1]["action_name"] == "campaign.launch"
        assert log[1]["outcome"] == "approval_needed"
        assert log[1]["reason_category"] == "spend_limit"

        # Check agent context included
        assert log[0]["agent_type"] == "CONTENT_SPECIALIST"


# ── Factory Function Tests ─────────────────────────────────────────────


class TestCreateGovernanceMiddleware:
    def test_factory_creates_middleware(self):
        middleware = create_governance_middleware(
            organization_id=uuid4(),
            autonomy_config=AutonomyConfig.create(
                organization_id=uuid4(),
                default_level=AutonomyLevel.SEMI_AUTO,
            ),
            agent_type="CONTENT_SPECIALIST",
        )
        assert isinstance(middleware, GovernanceMiddleware)
        assert middleware.agent_type == "CONTENT_SPECIALIST"

    def test_factory_defaults(self):
        """Factory should work with minimal parameters."""
        middleware = create_governance_middleware(
            organization_id=uuid4(),
        )
        assert isinstance(middleware, GovernanceMiddleware)
        assert middleware.agent_type == ""
        assert middleware.autonomy_config.default_level == AutonomyLevel.ADVISORY


# ── Tool-to-Action Mapping Tests ───────────────────────────────────────


class TestToolActionMapping:
    def test_content_generate_mapped(self):
        from astra_agent_orchestrator.governance import map_tool_to_action

        assert map_tool_to_action("generate_content") == "content.generate"

    def test_campaign_launch_mapped(self):
        from astra_agent_orchestrator.governance import map_tool_to_action

        assert map_tool_to_action("launch_campaign") == "campaign.launch"

    def test_unknown_tool_mapped(self):
        from astra_agent_orchestrator.governance import map_tool_to_action

        assert map_tool_to_action("unknown_tool") == "unknown.action"

    def test_all_known_tools_mapped(self):
        """Ensure all expected tools have mappings."""
        from astra_agent_orchestrator.governance import map_tool_to_action

        expected_mappings = {
            "generate_content": "content.generate",
            "generate_blog_post": "content.generate",
            "generate_social_post": "content.generate",
            "review_content": "content.review",
            "publish_content": "content.publish",
            "delete_content": "content.delete",
            "create_campaign": "campaign.create",
            "update_campaign": "campaign.update",
            "launch_campaign": "campaign.launch",
            "pause_campaign": "campaign.pause",
            "complete_campaign": "campaign.complete",
            "set_budget": "spend.allocate",
            "increase_budget": "spend.increase",
            "reallocate_budget": "budget.reallocate",
            "analyze_competitors": "research.competitors",
            "analyze_trends": "research.trends",
            "research_market": "research.analyze",
            "create_creative": "creative.create",
            "update_creative": "creative.update",
            "approve_creative": "creative.approve",
        }
        for tool, action in expected_mappings.items():
            assert map_tool_to_action(tool) == action, f"{tool} not mapped correctly"

    def test_action_map_completeness(self):
        """Ensure all mapped actions exist in risk classification."""
        from astra_agent_orchestrator.governance import TOOL_TO_ACTION_MAP, get_action_risk_level

        for tool, action in TOOL_TO_ACTION_MAP.items():
            risk = get_action_risk_level(action)
            assert risk in (0, 1, 2), f"Action {action} has invalid risk level {risk}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
