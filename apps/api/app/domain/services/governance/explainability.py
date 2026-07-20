"""Explainability Service — generates natural-language explanations for agent actions.

Per the Engineering Constitution (Article 2.6):
  "Every agent decision emits reasoning trace"
  "Every agent decision explainable in plain English"

This service:
1. Extracts reasoning traces from AgentAction records
2. Generates human-readable summaries
3. Supports decision replay (step-by-step walkthrough)
4. Formats explanations for different audiences (admin, auditor, end-user)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.domain.entities.governance.autonomy import AgentAction


@dataclass
class ExplanationOutput:
    """A formatted explanation of an agent's action."""

    action_id: str
    agent_type: str
    agent_id: str
    action: str
    resource_type: str
    resource_id: str

    # Summaries
    one_line: str = ""
    paragraph: str = ""
    detailed: str = ""

    # Structured data
    reasoning_steps: list[dict[str, Any]] = field(default_factory=list)
    autonomy_context: dict[str, Any] = field(default_factory=dict)
    outcome: dict[str, Any] = field(default_factory=dict)


class ExplainabilityService:
    """Stateless service that generates explanations for agent actions.

    Usage:
        service = ExplainabilityService()
        explanation = service.explain(action)
        summary = service.generate_summary(action)
        replay = service.replay_decision(action)
    """

    def explain(self, action: AgentAction) -> ExplanationOutput:
        """Generate a full explanation for an agent action."""
        return ExplanationOutput(
            action_id=str(action.id),
            agent_type=action.agent_type,
            agent_id=action.agent_id,
            action=action.action,
            resource_type=action.resource_type,
            resource_id=action.resource_id,
            one_line=self._generate_one_liner(action),
            paragraph=self._generate_paragraph(action),
            detailed=self._generate_detailed(action),
            reasoning_steps=action.reasoning_trace,
            autonomy_context={
                "level": action.autonomy_level.value,
                "was_auto_executed": action.was_auto_executed,
                "had_approval_request": action.approval_request_id is not None,
            },
            outcome={
                "success": action.success,
                "error": action.error_message,
            },
        )

    def generate_summary(self, action: AgentAction) -> str:
        """Generate a one-line summary of an action."""
        return self._generate_one_liner(action)

    def generate_paragraph(self, action: AgentAction) -> str:
        """Generate a paragraph-length explanation."""
        return self._generate_paragraph(action)

    def replay_decision(self, action: AgentAction) -> list[dict[str, Any]]:
        """Return the step-by-step reasoning trace for decision replay."""
        if not action.reasoning_trace:
            return [
                {
                    "step": 0,
                    "thought": action.reasoning or "No reasoning trace available.",
                    "action": action.action,
                    "result": "Action recorded."
                    if action.success
                    else f"Failed: {action.error_message}",
                }
            ]
        return action.reasoning_trace

    def generate_audit_summary(
        self,
        actions: list[AgentAction],
        organization_id: UUID,
    ) -> dict[str, Any]:
        """Generate a summary of all actions for a given organization.

        Useful for audit reviews and compliance reporting.
        """
        total = len(actions)
        successful = sum(1 for a in actions if a.success)
        failed = total - successful
        auto_executed = sum(1 for a in actions if a.was_auto_executed)
        human_approved = sum(1 for a in actions if a.approval_request_id is not None)
        total_cost = sum(a.cost_usd for a in actions)
        total_tokens = sum(a.tokens_used for a in actions)

        # Breakdown by agent type
        by_agent_type: dict[str, int] = {}
        for a in actions:
            by_agent_type[a.agent_type] = by_agent_type.get(a.agent_type, 0) + 1

        # Breakdown by action
        by_action: dict[str, int] = {}
        for a in actions:
            by_action[a.action] = by_action.get(a.action, 0) + 1

        # Autonomy level distribution
        by_level: dict[str, int] = {}
        for a in actions:
            level_name = a.autonomy_level.name
            by_level[level_name] = by_level.get(level_name, 0) + 1

        return {
            "organization_id": str(organization_id),
            "total_actions": total,
            "successful": successful,
            "failed": failed,
            "auto_executed": auto_executed,
            "human_approved": human_approved,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_agent_type": by_agent_type,
            "by_action": by_action,
            "by_autonomy_level": by_level,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_one_liner(self, action: AgentAction) -> str:
        """One-line summary."""
        agent_label = action.agent_type or "Unknown"
        agent_short = action.agent_id[:8] if action.agent_id else "?"

        parts = [f"{agent_label} agent ({agent_short}...)"]

        if action.action:
            parts.append(f"performed '{action.action}'")

        if action.resource_type:
            resource = action.resource_type
            if action.resource_id:
                resource += f" ({action.resource_id[:8]}...)"
            parts.append(f"on {resource}")

        if not action.success:
            parts.append(f"— FAILED: {action.error_message}")

        return " ".join(parts)

    def _generate_paragraph(self, action: AgentAction) -> str:
        """Paragraph-level explanation."""
        sentences = []

        # Who did what
        sentences.append(
            f"The {action.agent_type or 'unknown'} agent "
            f"(ID: {action.agent_id[:8]}...) executed the action "
            f"'{action.action}' targeting {action.resource_type or 'unknown resource'} "
            f"'{action.resource_id}'."
        )

        # Reasoning
        if action.reasoning:
            sentences.append(f'Its reasoning was: "{action.reasoning}"')

        # Autonomy context
        if action.was_auto_executed:
            sentences.append(
                f"This action was auto-executed at autonomy level "
                f"{action.autonomy_level.name} (level {action.autonomy_level.value})."
            )
        elif action.approval_request_id:
            sentences.append(
                f"This action required human approval "
                f"(approval request: {action.approval_request_id})."
            )

        # Cost
        if action.tokens_used > 0:
            sentences.append(
                f"AI cost: {action.tokens_used:,} tokens (${action.cost_usd:.4f}) "
                f"using model '{action.model_used}'."
            )

        # Outcome
        if action.success:
            sentences.append("The action completed successfully.")
        else:
            sentences.append(f"The action FAILED with error: {action.error_message}")

        return " ".join(sentences)

    def _generate_detailed(self, action: AgentAction) -> str:
        """Detailed explanation with reasoning trace."""
        sections = [
            "=== Action Explanation ===",
            f"Action: {action.action}",
            f"Agent: {action.agent_type} ({action.agent_id})",
            f"Resource: {action.resource_type} ({action.resource_id})",
            f"Timestamp: {action.created_at.isoformat()}",
            f"Autonomy Level: {action.autonomy_level.name} ({action.autonomy_level.value})",
            f"Auto-Executed: {action.was_auto_executed}",
            "",
        ]

        if action.reasoning:
            sections.append(f"Reasoning: {action.reasoning}")
            sections.append("")

        if action.reasoning_trace:
            sections.append("--- Decision Steps ---")
            for step in action.reasoning_trace:
                step_num = step.get("step", "?")
                thought = step.get("thought", "")
                action_taken = step.get("action", "")
                result = step.get("result", "")
                sections.append(f"  Step {step_num}: {thought}")
                if action_taken:
                    sections.append(f"    Action: {action_taken}")
                if result:
                    sections.append(f"    Result: {result}")
            sections.append("")

        if action.approval_request_id:
            sections.append(f"Approval Request: {action.approval_request_id}")
            sections.append("")

        sections.append(f"Outcome: {'SUCCESS' if action.success else 'FAILED'}")
        if not action.success:
            sections.append(f"Error: {action.error_message}")

        if action.tokens_used > 0:
            sections.append(
                f"Cost: {action.tokens_used:,} tokens, "
                f"${action.cost_usd:.4f}, model: {action.model_used}"
            )

        if action.details:
            sections.append(f"Details: {action.details}")

        return "\n".join(sections)
