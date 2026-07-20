"""Autonomy Enforcement Service — runtime gate for agent actions.

Called by agents before executing any action. Determines whether the
action can proceed automatically or requires human approval based on:
1. The organization's autonomy config
2. The action's risk level
3. Any explicit approval rules that match

This is a stateless domain service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.entities.governance.approval import (
    ApprovalRule,
)
from app.domain.entities.governance.autonomy import (
    AgentAction,
    AutonomyConfig,
    AutonomyLevel,
    get_action_risk_level,
)
from app.domain.services.governance.approval_service import (
    ApprovalEvaluationResult,
    ApprovalEvaluationService,
)


@dataclass
class EnforcementResult:
    """Result of autonomy enforcement check."""

    allowed: bool = False
    reason: str = ""
    autonomy_level: AutonomyLevel = AutonomyLevel.ADVISORY
    risk_level: int = 0
    requires_approval: bool = False
    approval_result: ApprovalEvaluationResult | None = None
    action_record: AgentAction | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "autonomy_level": self.autonomy_level.value,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
        }


class AutonomyEnforcementService:
    """Stateless service that checks whether an agent action is permitted.

    Usage:
        service = AutonomyEnforcementService()
        result = service.check(config, rules, action, agent_type)
        if not result.allowed:
            # Create approval request, don't execute
        elif result.requires_approval:
            # Execute but hold for approval
    """

    def __init__(self, approval_service: ApprovalEvaluationService | None = None):
        self._approval_service = approval_service or ApprovalEvaluationService()

    def check(
        self,
        config: AutonomyConfig,
        rules: list[ApprovalRule],
        action: AgentAction,
        agent_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> EnforcementResult:
        """Check whether an agent action is permitted.

        Args:
            config: Organization's autonomy configuration.
            rules: Active approval rules for the organization.
            action: The agent action to check.
            agent_type: Override agent type (defaults to action.agent_type).
            context: Additional context for rule evaluation.

        Returns:
            EnforcementResult with allow/deny and reasoning.

        """
        agent_type = agent_type or action.agent_type
        risk_level = get_action_risk_level(action.action)
        level = config.get_level_for_action(action.action, agent_type)

        result = EnforcementResult(
            autonomy_level=level,
            risk_level=risk_level,
            action_record=action,
        )

        # FULL_AUTO: allow everything
        if level == AutonomyLevel.FULL_AUTO:
            # Even at FULL_AUTO, check if any approval rules mandate human review
            if rules:
                eval_ctx = context or self._build_default_context(action)
                eval_result = self._approval_service.evaluate(rules, eval_ctx)
                if eval_result.requires_approval:
                    result.requires_approval = True
                    result.approval_result = eval_result
                    result.allowed = False
                    result.reason = (
                        f"Approval required by rule(s): {', '.join(eval_result.triggered_rule_ids)}"
                    )
                    return result

            result.allowed = True
            result.reason = "Full autonomy — auto-executed"
            action.record_auto_executed(level)
            return result

        # SEMI_AUTO: allow low-risk, block high-risk
        if level == AutonomyLevel.SEMI_AUTO:
            if risk_level >= 2:
                result.allowed = False
                result.requires_approval = True
                result.reason = (
                    f"High-risk action '{action.action}' (risk={risk_level}) "
                    f"requires approval at SEMI_AUTO level"
                )
                # Check approval rules for additional context
                if rules:
                    eval_ctx = context or self._build_default_context(action)
                    eval_result = self._approval_service.evaluate(rules, eval_ctx)
                    if eval_result.requires_approval:
                        result.approval_result = eval_result
                return result

            if risk_level <= 1:
                # Check spend limit
                spend_amount = self._extract_spend_amount(context or {}, action)
                if spend_amount > config.auto_approve_spend_limit:
                    result.allowed = False
                    result.requires_approval = True
                    result.reason = (
                        f"Spend amount ${spend_amount:.2f} exceeds auto-approve "
                        f"limit of ${config.auto_approve_spend_limit:.2f}"
                    )
                    return result

                result.allowed = True
                result.reason = (
                    f"Low-risk action '{action.action}' auto-executed at SEMI_AUTO level"
                )
                action.record_auto_executed(level)
                return result

        # ADVISORY: nothing auto-executes
        result.allowed = False
        result.requires_approval = True
        result.reason = f"ADVISORY level — action '{action.action}' requires human approval"
        if rules:
            eval_ctx = context or self._build_default_context(action)
            eval_result = self._approval_service.evaluate(rules, eval_ctx)
            if eval_result.requires_approval:
                result.approval_result = eval_result
        return result

    def check_simple(
        self,
        config: AutonomyConfig,
        action_name: str,
        agent_type: str,
        organization_id: UUID,
        agent_id: str = "",
        spend_amount: float = 0.0,
    ) -> EnforcementResult:
        """Simplified check — creates AgentAction internally."""
        action = AgentAction.create(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action_name,
        )
        context: dict[str, Any] = {}
        if spend_amount > 0:
            context["amount"] = spend_amount
        return self.check(config, [], action, agent_type, context)

    def _build_default_context(self, action: AgentAction) -> dict[str, Any]:
        """Build a default context from action details."""
        ctx: dict[str, Any] = {
            "action": action.action,
            "resource_type": action.resource_type,
            "resource_id": action.resource_id,
        }
        if action.details:
            ctx.update(action.details)
        return ctx

    def _extract_spend_amount(self, context: dict[str, Any], action: AgentAction) -> float:
        """Extract spend amount from context or action details."""
        amount = context.get("amount", 0.0)
        if not amount:
            amount = action.details.get("amount", 0.0)
        if not amount:
            amount = action.details.get("budget_amount", 0.0)
        return float(amount)
