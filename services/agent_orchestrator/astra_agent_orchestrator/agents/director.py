"""Director Agents — Mid-level orchestrators for domain-specific work.

Directors receive tasks from the CEO, further decompose them, and delegate
to specialist agents within their domain.
"""

import json
import logging
from typing import Any
from uuid import UUID, uuid4

from ..agent import AgentConfig, AgentType
from .base import ReActAgent

logger = logging.getLogger(__name__)

# Director-specific configurations
DIRECTOR_CONFIGS: dict[AgentType, dict[str, Any]] = {
    AgentType.MARKETING_DIRECTOR: {
        "name": "Marketing Director",
        "description": "Orchestrates marketing strategy across channels",
        "capabilities": [
            "planning",
            "delegation",
            "campaign_strategy",
            "brand_management",
        ],
        "system_prompt": """You are the Marketing Director of ASTRA OS.
You orchestrate marketing campaigns by delegating to specialists:
- Content Specialist: blog posts, articles, copywriting
- SEO Specialist: keyword research, on-page optimization
- Social Media Specialist: social content, engagement strategy

When given a marketing task, decompose it into specialist tasks.
Return a JSON with your decomposition:
{
  "thought": "Your marketing strategy reasoning",
  "action": null,
  "action_input": null,
  "final_answer": null,
  "decomposition": {
    "tasks": [
      {
        "specialist": "CONTENT_SPECIALIST",
        "task": "specific task",
        "requirements": ["req1"],
        "priority": "high"
      }
    ]
  }
}""",
        "subordinates": [
            AgentType.CONTENT_SPECIALIST,
            AgentType.SEO_SPECIALIST,
            AgentType.SOCIAL_SPECIALIST,
        ],
    },
    AgentType.CREATIVE_DIRECTOR: {
        "name": "Creative Director",
        "description": "Ensures brand consistency and creative quality",
        "capabilities": [
            "brand_voice",
            "design_review",
            "creative_direction",
            "approval",
        ],
        "system_prompt": """You are the Creative Director of ASTRA OS.
You ensure all creative output aligns with brand guidelines.
Delegate to: Copywriter, Designer, Brand Voice specialists.
Review and approve creative work.""",
        "subordinates": [
            AgentType.COPYWRITER,
            AgentType.DESIGNER,
            AgentType.BRAND_VOICE,
        ],
    },
    AgentType.ADVERTISING_DIRECTOR: {
        "name": "Advertising Director",
        "description": "Manages paid advertising and campaign optimization",
        "capabilities": [
            "campaign_optimization",
            "bidding",
            "audience_targeting",
            "budget",
        ],
        "system_prompt": """You are the Advertising Director of ASTRA OS.
You manage paid campaigns across platforms.
Delegate to: Campaign Optimizer, Bid Manager, Audience Researcher.
Optimize for ROI and conversion.""",
        "subordinates": [
            AgentType.CAMPAIGN_OPTIMIZER,
            AgentType.BID_MANAGER,
            AgentType.AUDIENCE_RESEARCHER,
        ],
    },
    AgentType.RESEARCH_DIRECTOR: {
        "name": "Research Director",
        "description": "Leads market and competitive research",
        "capabilities": [
            "market_research",
            "competitor_analysis",
            "trend_analysis",
        ],
        "system_prompt": """You are the Research Director of ASTRA OS.
You lead research initiatives.
Delegate to: Market Researcher, Competitor Analyst, Trend Analyzer.""",
        "subordinates": [
            AgentType.MARKET_RESEARCHER,
            AgentType.COMPETITOR_ANALYST,
            AgentType.TREND_ANALYZER,
        ],
    },
    AgentType.ANALYTICS_DIRECTOR: {
        "name": "Analytics Director",
        "description": "Oversees data analysis and reporting",
        "capabilities": [
            "data_analysis",
            "attribution",
            "reporting",
            "visualization",
        ],
        "system_prompt": """You are the Analytics Director of ASTRA OS.
You oversee data analysis and performance reporting.
Delegate to: Data Analyst, Attribution Modeler, Report Generator.""",
        "subordinates": [
            AgentType.DATA_ANALYST,
            AgentType.ATTRIBUTION_MODELER,
            AgentType.REPORT_GENERATOR,
        ],
    },
    AgentType.WORKFLOW_DIRECTOR: {
        "name": "Workflow Director",
        "description": "Manages automation and integration workflows",
        "capabilities": [
            "workflow_design",
            "automation",
            "integration",
            "scheduling",
        ],
        "system_prompt": """You are the Workflow Director of ASTRA OS.
You design and manage automated workflows.
Delegate to: Workflow Builder, Automation Scheduler, Integration Manager.""",
        "subordinates": [
            AgentType.WORKFLOW_BUILDER,
            AgentType.AUTOMATION_SCHEDULER,
            AgentType.INTEGRATION_MANAGER,
        ],
    },
    AgentType.COMPLIANCE_DIRECTOR: {
        "name": "Compliance Director",
        "description": "Ensures regulatory compliance and brand safety",
        "capabilities": [
            "content_review",
            "privacy",
            "policy_enforcement",
            "audit",
        ],
        "system_prompt": """You are the Compliance Director of ASTRA OS.
You ensure all content and activities comply with regulations and policies.
Delegate to: Content Reviewer, Privacy Auditor, Policy Enforcer.""",
        "subordinates": [
            AgentType.CONTENT_REVIEWER,
            AgentType.PRIVACY_AUDITOR,
            AgentType.POLICY_ENFORCER,
        ],
    },
}


class DirectorAgent(ReActAgent):
    """Director-level agent that orchestrates specialists within a domain.

    Each director has a specific domain (marketing, creative, etc.) and
    delegates tasks to specialist agents.
    """

    def __init__(
        self,
        agent_type: AgentType,
        config: AgentConfig | None = None,
        tenant_id: UUID | None = None,
        **kwargs: Any,
    ):
        if config is None:
            dir_config = DIRECTOR_CONFIGS.get(agent_type, {})
            config = AgentConfig(
                agent_type=agent_type,
                name=dir_config.get("name", f"{agent_type.value} Director"),
                description=dir_config.get(
                    "description",
                    f"Director for {agent_type.value}",
                ),
                capabilities=dir_config.get("capabilities", ["planning", "delegation"]),
                autonomy_level=1,
                max_iterations=8,
                temperature=0.7,
                system_prompt=dir_config.get("system_prompt", ""),
            )
        if tenant_id:
            config.tenant_id = tenant_id
        super().__init__(config=config, tenant_id=tenant_id or uuid4(), **kwargs)
        self._dir_config = DIRECTOR_CONFIGS.get(agent_type, {})
        self._subordinates: list[AgentType] = self._dir_config.get("subordinates", [])

    def get_system_prompt(self) -> str:
        return self.config.system_prompt or (
            f"You are the {self.config.name}. Delegate tasks to your specialist team members."
        )

    def prepare_input(self, input_data: Any) -> str:
        """Format the director's task."""
        if isinstance(input_data, dict):
            task = input_data.get("task", input_data)
            return (
                f"Task from CEO: {json.dumps(task, default=str)}\n"
                f"Your subordinates: {[s.value for s in self._subordinates]}"
            )
        return f"Task: {input_data}\nSubordinates: {[s.value for s in self._subordinates]}"

    @property
    def subordinates(self) -> list[AgentType]:
        """Return the list of specialist agent types this director can delegate to."""
        return list(self._subordinates)
