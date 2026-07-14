"""Agent Governance Middleware — runtime enforcement of autonomy and approval.

This middleware intercepts agent tool calls and checks them against the
organization's autonomy configuration and approval rules before execution.

Usage:
    from services.agent_orchestrator.governance import GovernanceMiddleware

    middleware = GovernanceMiddleware(organization_id=org_id)
    # Inject into agent or use standalone

Per M3 exit criteria:
  "Autonomy level enforced at runtime (agent checks before action)"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from apps.api.app.domain.entities.governance.autonomy import (
    AutonomyConfig,
    AutonomyLevel,
    get_action_risk_level,
)

logger = logging.getLogger(__name__)


# Map tool names to governance action names
# This allows mapping LLM tool names to the governance risk system
TOOL_TO_ACTION_MAP: dict[str, str] = {
    # Content tools
    "generate_content": "content.generate",
    "generate_blog_post": "content.generate",
    "generate_social_post": "content.generate",
    "review_content": "content.review",
    "publish_content": "content.publish",
    "delete_content": "content.delete",

    # Campaign tools
    "create_campaign": "campaign.create",
    "update_campaign": "campaign.update",
    "launch_campaign": "campaign.launch",
    "pause_campaign": "campaign.pause",
    "complete_campaign": "campaign.complete",

    # Budget tools
    "set_budget": "spend.allocate",
    "increase_budget": "spend.increase",
    "reallocate_budget": "budget.reallocate",

    # Analytics tools
    "query_analytics": "analytics.query",
    "generate_report": "analytics.report",

    # Research tools
    "analyze_competitors": "research.competitors",
    "analyze_trends": "research.trends",
    "research_market": "research.analyze",

    # Creative tools
    "create_creative": "creative.create",
    "update_creative": "creative.update",
    "approve_creative": "creative.approve",

    # Bid/audience tools
    "update_bid": "bid.update",
    "target_audience": "audience.target",
    "update_schedule": "schedule.update",

    # Account tools
    "connect_account": "account.connect",
    "disconnect_account": "account.disconnect",
}


def map_tool_to_action(tool_name: str) -> str:
    """Map a tool name to a governance action name."""
    return TOOL_TO_ACTION_MAP.get(tool_name, "unknown.action")


@dataclass
class GovernanceCheckResult:
    """Result of a governance check on a tool call."""

    allowed: bool = False
    requires_approval: bool = False
    blocked: bool = False
    reason: str = ""
    action_name: str = ""
    risk_level: int = 0
    autonomy_level: int = 0
    approval_request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "blocked": self.blocked,
            "reason": self.reason,
            "action_name": self.action_name,
            "risk_level": self.risk_level,
            "autonomy_level": self.autonomy_level,
        }


class GovernanceMiddleware:
    """Middleware that enforces governance rules on agent tool calls.

    This is designed to be used in two modes:
    1. Standalone: Check tool calls before agent execution
    2. Integrated: Inject into Agent.call_tool() for automatic enforcement

    The middleware uses the same AutonomyConfig and risk classification as
    the API-layer CheckAgentActionUseCase, but operates at the agent
    runtime level without requiring a DB connection (uses in-memory config).
    """

    def __init__(
        self,
        organization_id: UUID,
        autonomy_config: AutonomyConfig | None = None,
        agent_type: str = "",
        agent_id: str = "",
        tool_action_map: dict[str, str] | None = None,
    ):
        self.organization_id = organization_id
        self.autonomy_config = autonomy_config or AutonomyConfig.create(organization_id)
        self.agent_type = agent_type
        self.agent_id = agent_id
        self._tool_action_map = tool_action_map or TOOL_TO_ACTION_MAP
        self._action_log: list[dict[str, Any]] = []

    def check_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> GovernanceCheckResult:
        """Check if a tool call is permitted by the governance config.

        Args:
            tool_name: The name of the tool the agent wants to call.
            parameters: Tool parameters (may contain spend amounts, etc.)

        Returns:
            GovernanceCheckResult with allow/block/requires_approval status.

        """
        action_name = self._tool_action_map.get(tool_name, "unknown.action")
        risk_level = get_action_risk_level(action_name)
        level = self.autonomy_config.get_level_for_action(action_name, self.agent_type)

        result = GovernanceCheckResult(
            action_name=action_name,
            risk_level=risk_level,
            autonomy_level=level.value,
        )

        # Extract spend amount from parameters
        spend_amount = 0.0
        if parameters:
            spend_amount = float(
                parameters.get("amount", 0)
                or parameters.get("budget_amount", 0)
                or parameters.get("spend_amount", 0)
                or 0
            )

        # FULL_AUTO: allow everything (audit only)
        if level == AutonomyLevel.FULL_AUTO:
            result.allowed = True
            result.reason = f"FULL_AUTO: '{tool_name}' auto-executed"
            self._log_action(action_name, "allowed", "full_auto")
            return result

        # SEMI_AUTO: allow low-risk, block high-risk
        if level == AutonomyLevel.SEMI_AUTO:
            if risk_level >= 2:
                result.blocked = True
                result.requires_approval = True
                result.reason = (
                    f"High-risk tool '{tool_name}' (action={action_name}, "
                    f"risk={risk_level}) requires approval at SEMI_AUTO"
                )
                self._log_action(action_name, "blocked", "semi_auto_high_risk")
                return result

            # Check spend limit
            if spend_amount > self.autonomy_config.auto_approve_spend_limit:
                result.requires_approval = True
                result.reason = (
                    f"Spend ${spend_amount:.2f} exceeds auto-approve limit "
                    f"${self.autonomy_config.auto_approve_spend_limit:.2f}"
                )
                self._log_action(action_name, "approval_needed", "spend_limit")
                return result

            result.allowed = True
            result.reason = f"SEMI_AUTO: '{tool_name}' low-risk auto-executed"
            self._log_action(action_name, "allowed", "semi_auto_low_risk")
            return result

        # ADVISORY: nothing auto-executes
        result.blocked = True
        result.requires_approval = True
        result.reason = (
            f"ADVISORY: tool '{tool_name}' requires human approval"
        )
        self._log_action(action_name, "blocked", "advisory")
        return result

    def get_action_log(self) -> list[dict[str, Any]]:
        """Get the log of all governance checks performed."""
        return list(self._action_log)

    def clear_action_log(self) -> None:
        """Clear the action log."""
        self._action_log.clear()

    def _log_action(self, action_name: str, outcome: str, reason_category: str) -> None:
        """Log a governance decision for auditing."""
        self._action_log.append({
            "organization_id": str(self.organization_id),
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "action_name": action_name,
            "outcome": outcome,
            "reason_category": reason_category,
        })


def create_governance_middleware(
    organization_id: UUID,
    autonomy_config: AutonomyConfig | None = None,
    agent_type: str = "",
    agent_id: str = "",
) -> GovernanceMiddleware:
    """Factory function for creating governance middleware."""
    return GovernanceMiddleware(
        organization_id=organization_id,
        autonomy_config=autonomy_config,
        agent_type=agent_type,
        agent_id=agent_id,
    )
