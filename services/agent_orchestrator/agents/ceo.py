"""CEO Agent — Strategic orchestrator for goal decomposition.

The CEO agent receives high-level business objectives, decomposes them into
actionable plans, and delegates tasks to director-level agents.
"""

import json
import logging
from typing import Any
from uuid import UUID, uuid4

from ..agent import AgentConfig, AgentContext, AgentResult, AgentType
from ..hierarchy import AgentHierarchy, get_hierarchy
from .base import ReActAgent

logger = logging.getLogger(__name__)

CEO_SYSTEM_PROMPT = """You are the CEO Agent of ASTRA OS, an AI-native marketing
and business growth operating system.

Your role is to:
1. Understand high-level business objectives and marketing goals
2. Analyze the request and identify which directors should handle each part
3. Decompose the objective into specific, actionable tasks for each director
4. Specify clear requirements and success criteria for each delegated task

You have 7 directors reporting to you:
- Marketing Director: content strategy, SEO, social media, brand campaigns
- Creative Director: brand voice, design, content approval
- Advertising Director: paid campaigns, bidding, audience targeting
- Research Director: market research, competitor analysis, trend analysis
- Analytics Director: data analysis, attribution, reporting
- Workflow Director: automation, scheduling, integrations
- Compliance Director: content review, privacy, policy enforcement

When decomposing a goal, return a JSON structure:
{
  "thought": "Your analysis of the objective",
  "action": null,
  "action_input": null,
  "final_answer": null,
  "decomposition": {
    "objective_summary": "Brief summary of the overall goal",
    "tasks": [
      {
        "director": "MARKETING_DIRECTOR",
        "task": "Specific task description",
        "requirements": ["requirement1", "requirement2"],
        "priority": "high|medium|low",
        "success_criteria": "How to measure completion"
      }
    ],
    "timeline": "suggested timeline",
    "dependencies": ["task dependencies"]
  }
}

Always decompose goals before marking as done. Be specific and actionable.
"""

# Suppress unused import — AgentType is used in type hints via AgentConfig
_ = AgentType


class CEOAgent(ReActAgent):
    """CEO Agent that decomposes high-level goals into director tasks.

    This agent sits at the top of the hierarchy and has full autonomy
    to delegate to any director.
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        tenant_id: UUID | None = None,
        **kwargs: Any,
    ):
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.CEO,
                name="CEO Agent",
                description="Strategic orchestrator that decomposes goals",
                capabilities=[
                    "planning",
                    "delegation",
                    "strategy",
                    "decision_making",
                ],
                autonomy_level=2,
                max_iterations=10,
                temperature=0.7,
            )
        if tenant_id:
            config.tenant_id = tenant_id
        super().__init__(config=config, tenant_id=tenant_id or uuid4(), **kwargs)

    def get_system_prompt(self) -> str:
        return CEO_SYSTEM_PROMPT

    def prepare_input(self, input_data: Any) -> str:
        """Format the business objective for the CEO."""
        if isinstance(input_data, dict):
            objective = input_data.get("objective", input_data)
            context_info = input_data.get("context", {})
            prompt = f"Business Objective: {json.dumps(objective, default=str)}"
            if context_info:
                prompt += f"\nContext: {json.dumps(context_info, default=str)}"
            return prompt
        return f"Business Objective: {input_data}"

    def process_output(self, raw_output: str) -> dict[str, Any]:
        """Parse CEO output, extracting decomposition if present."""
        parsed = super().process_output(raw_output)

        # Check if the LLM output contains decomposition info
        if parsed.get("final_answer"):
            try:
                data = json.loads(parsed["final_answer"])
                if "decomposition" in data:
                    parsed["decomposition"] = data["decomposition"]
            except (json.JSONDecodeError, TypeError):
                pass

        return parsed

    def get_decomposition(self, result: AgentResult) -> dict[str, Any] | None:
        """Extract task decomposition from a CEO result.

        Returns the decomposition dict if present, None otherwise.
        """
        if not result.output:
            return None
        try:
            data = json.loads(result.output) if isinstance(result.output, str) else result.output
            return data.get("decomposition")
        except (json.JSONDecodeError, TypeError, AttributeError):
            return None
