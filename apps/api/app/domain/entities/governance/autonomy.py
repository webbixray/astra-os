"""Autonomy Levels — controls how much independence agents have.

Levels:
- ADVISORY (0): Agent only suggests, human makes all decisions
- SEMI_AUTO (1): Agent executes low-risk actions, escalation for high-risk
- FULL_AUTO (2): Agent executes all actions, audit log only

Configuration is per-agent-type, per-tenant (organization).
A ComplianceDirector agent can override autonomy at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


class AutonomyLevel(int, Enum):
    """How much independence an agent has."""

    ADVISORY = 0  # Suggestions only — human approves everything
    SEMI_AUTO = 1  # Low-risk auto, high-risk needs approval
    FULL_AUTO = 2  # Full automation — audit log only


# Risk classification for common agent actions
ACTION_RISK_LEVELS: dict[str, int] = {
    # Low risk (SEMI_AUTO can execute)
    "content.generate": 1,
    "content.review": 1,
    "analytics.report": 1,
    "analytics.query": 1,
    "research.analyze": 1,
    "research.competitors": 1,
    "research.trends": 1,
    "workflow.status": 1,
    # Medium risk (needs approval at ADVISORY)
    "campaign.create": 1,
    "campaign.update": 1,
    "creative.create": 1,
    "creative.update": 1,
    "creative.approve": 1,
    "bid.update": 1,
    "audience.target": 1,
    "schedule.update": 1,
    # High risk (needs approval even at SEMI_AUTO)
    "campaign.launch": 2,
    "campaign.pause": 2,
    "campaign.complete": 2,
    "spend.allocate": 2,
    "spend.increase": 2,
    "budget.reallocate": 2,
    "content.publish": 2,
    "content.delete": 2,
    "account.connect": 2,
    "account.disconnect": 2,
    "policy.override": 2,
}


def get_action_risk_level(action: str) -> int:
    """Get the risk level for an action (0=none, 1=low, 2=high)."""
    return ACTION_RISK_LEVELS.get(action, 1)  # Default to low risk


@dataclass
class AutonomyConfig:
    """Per-organization autonomy configuration.

    Defines the autonomy level for each agent type within an organization.
    Can be overridden at the individual agent level.
    """

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Default level for all agents in this org
    default_level: AutonomyLevel = AutonomyLevel.ADVISORY

    # Per-agent-type overrides
    agent_levels: dict[str, AutonomyLevel] = field(default_factory=dict)

    # Per-action overrides (action → required level)
    action_overrides: dict[str, AutonomyLevel] = field(default_factory=dict)

    # Maximum spend per action without approval (at SEMI_AUTO level)
    auto_approve_spend_limit: float = 100.0
    auto_approve_currency: str = "USD"

    # Enabled channels for auto-execution
    auto_execute_channels: list[str] = field(default_factory=list)

    # Created/updated
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        default_level: AutonomyLevel = AutonomyLevel.ADVISORY,
        auto_approve_spend_limit: float = 100.0,
    ) -> AutonomyConfig:
        if auto_approve_spend_limit < 0:
            raise ValidationError("Spend limit cannot be negative")
        return cls(
            organization_id=organization_id,
            default_level=default_level,
            auto_approve_spend_limit=auto_approve_spend_limit,
        )

    def get_level_for_agent(self, agent_type: str) -> AutonomyLevel:
        """Get the autonomy level for a specific agent type."""
        return self.agent_levels.get(agent_type, self.default_level)

    def set_agent_level(self, agent_type: str, level: AutonomyLevel) -> None:
        """Set autonomy level for a specific agent type."""
        self.agent_levels[agent_type] = level
        self.updated_at = now()

    def get_level_for_action(self, action: str, agent_type: str | None = None) -> AutonomyLevel:
        """Get the effective autonomy level for a specific action.

        Priority: action_override > agent_level > default_level
        """
        if action in self.action_overrides:
            return self.action_overrides[action]
        if agent_type and agent_type in self.agent_levels:
            return self.agent_levels[agent_type]
        return self.default_level

    def can_auto_execute(
        self, action: str, amount: float = 0.0, agent_type: str | None = None
    ) -> bool:
        """Determine if an action can be auto-executed without approval.

        Returns True if the action is within the autonomy level and spend limits.
        """
        level = self.get_level_for_action(action, agent_type)
        risk = get_action_risk_level(action)

        if level == AutonomyLevel.FULL_AUTO:
            return True

        if level == AutonomyLevel.SEMI_AUTO:
            if risk >= 2:
                return False  # High risk always needs approval
            if amount > self.auto_approve_spend_limit:
                return False  # Over spend limit
            return True

        # ADVISORY — nothing auto-executes
        return False


@dataclass
class AgentAction:
    """Records an agent action for audit and explainability.

    Every action an agent takes is recorded with:
    - What was done (action, resource, details)
    - Why (reasoning, rule references)
    - Outcome (success, failure, blocked)
    - Autonomy context (level, was auto-executed)
    """

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    agent_type: str = ""

    # Action details
    action: str = ""  # e.g., "campaign.launch"
    resource_type: str = ""  # e.g., "campaign"
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    # Reasoning
    reasoning: str = ""  # Natural language explanation
    reasoning_trace: list[dict[str, Any]] = field(default_factory=list)
    # Step-by-step reasoning: [{"step": 1, "thought": "...", "action": "...", "result": "..."}]

    # Autonomy context
    autonomy_level: AutonomyLevel = AutonomyLevel.ADVISORY
    was_auto_executed: bool = False
    approval_request_id: UUID | None = None

    # Outcome
    success: bool = True
    error_message: str = ""
    result: dict[str, Any] = field(default_factory=dict)

    # Cost tracking
    tokens_used: int = 0
    cost_usd: float = 0.0
    model_used: str = ""

    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        agent_id: str,
        agent_type: str,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        reasoning: str = "",
    ) -> AgentAction:
        return cls(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reasoning=reasoning,
        )

    def record_approval_needed(self, request_id: UUID) -> None:
        """Mark this action as requiring approval."""
        self.approval_request_id = request_id
        self.was_auto_executed = False

    def record_auto_executed(self, level: AutonomyLevel) -> None:
        """Mark this action as auto-executed."""
        self.autonomy_level = level
        self.was_auto_executed = True

    def record_success(self, result: dict[str, Any] | None = None) -> None:
        """Mark action as successful."""
        self.success = True
        self.result = result or {}

    def record_failure(self, error: str) -> None:
        """Mark action as failed."""
        self.success = False
        self.error_message = error

    def add_reasoning_step(
        self,
        step: int,
        thought: str,
        action_taken: str = "",
        result: str = "",
    ) -> None:
        """Add a step to the reasoning trace."""
        self.reasoning_trace.append(
            {
                "step": step,
                "thought": thought,
                "action": action_taken,
                "result": result,
            }
        )

    def to_explanation(self) -> str:
        """Generate a natural language explanation of this action."""
        parts = [
            f"Agent {self.agent_type} ({self.agent_id[:8]}...) "
            f"performed '{self.action}' on {self.resource_type} '{self.resource_id}'.",
        ]

        if self.reasoning:
            parts.append(f"Reasoning: {self.reasoning}")

        if self.was_auto_executed:
            parts.append(f"Auto-executed at autonomy level {self.autonomy_level.value}.")
        elif self.approval_request_id:
            parts.append(f"Required human approval (request {self.approval_request_id}).")

        if self.reasoning_trace:
            parts.append("Decision steps:")
            for step in self.reasoning_trace:
                parts.append(f"  {step['step']}. {step['thought']}")

        if not self.success:
            parts.append(f"Failed: {self.error_message}")

        return " ".join(parts)
