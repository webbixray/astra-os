"""Approval Evaluation Service — evaluates rules against action context.

This is a stateless domain service. Given a set of active rules and an
action context, it determines whether human approval is required and
which rules were triggered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.governance.approval import ApprovalRule


@dataclass
class ApprovalEvaluationResult:
    """Result of evaluating approval rules against an action context."""

    requires_approval: bool = False
    triggered_rules: list[ApprovalRule] = field(default_factory=list)
    triggered_rule_ids: list[str] = field(default_factory=list)
    all_approver_roles: list[str] = field(default_factory=list)
    highest_priority: int = 0

    def add_triggered_rule(self, rule: ApprovalRule) -> None:
        """Add a triggered rule to the result."""
        self.requires_approval = True
        self.triggered_rules.append(rule)
        self.triggered_rule_ids.append(str(rule.id))
        for role in rule.approver_roles:
            if role not in self.all_approver_roles:
                self.all_approver_roles.append(role)
        self.highest_priority = max(self.highest_priority, rule.priority)


class ApprovalEvaluationService:
    """Evaluates approval rules against an action context.

    Stateless service — all state comes from the rules and context passed in.
    """

    def evaluate(
        self,
        rules: list[ApprovalRule],
        context: dict[str, Any],
    ) -> ApprovalEvaluationResult:
        """Evaluate all active rules against the given context.

        Args:
            rules: All approval rules for the organization.
            context: Action context (amount, text, channel, is_new_audience, etc.)

        Returns:
            ApprovalEvaluationResult with triggered rules and approval status.

        """
        result = ApprovalEvaluationResult()

        # Sort by priority (highest first) for deterministic ordering
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if rule.evaluate(context):
                result.add_triggered_rule(rule)

        return result

    def evaluate_spend(
        self,
        rules: list[ApprovalRule],
        amount: float,
        currency: str = "USD",
    ) -> ApprovalEvaluationResult:
        """Convenience method to evaluate spend-related rules."""
        return self.evaluate(rules, {"amount": amount, "currency": currency})

    def evaluate_content(
        self,
        rules: list[ApprovalRule],
        text: str,
        content_type: str = "",
    ) -> ApprovalEvaluationResult:
        """Convenience method to evaluate content-related rules."""
        return self.evaluate(rules, {"text": text, "content_type": content_type})

    def evaluate_audience(
        self,
        rules: list[ApprovalRule],
        is_new_audience: bool,
        audience_name: str = "",
    ) -> ApprovalEvaluationResult:
        """Convenience method to evaluate audience-related rules."""
        return self.evaluate(rules, {
            "is_new_audience": is_new_audience,
            "audience_name": audience_name,
        })

    def evaluate_channel(
        self,
        rules: list[ApprovalRule],
        channel: str,
    ) -> ApprovalEvaluationResult:
        """Convenience method to evaluate channel-related rules."""
        return self.evaluate(rules, {"channel": channel})
