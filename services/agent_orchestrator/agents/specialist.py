"""Specialist Agents — Domain experts that execute specific tasks.

Specialists are leaf nodes in the agent hierarchy. They receive concrete
tasks and execute them using their domain expertise and available tools.
"""

import json
import logging
from typing import Any
from uuid import UUID, uuid4

from ..agent import AgentConfig, AgentType
from .base import ReActAgent

logger = logging.getLogger(__name__)

# Specialist-specific configurations
SPECIALIST_CONFIGS: dict[AgentType, dict[str, Any]] = {
    AgentType.CONTENT_SPECIALIST: {
        "name": "Content Specialist",
        "description": "Creates blog posts, articles, and marketing copy",
        "capabilities": ["content_creation", "copywriting", "editing"],
        "system_prompt": (
            "You are a Content Specialist. Create high-quality marketing "
            "content including blog posts, articles, social media copy, "
            "and email campaigns. Focus on engagement and conversion."
        ),
    },
    AgentType.SEO_SPECIALIST: {
        "name": "SEO Specialist",
        "description": "Optimizes content for search engines",
        "capabilities": ["keyword_research", "on_page_seo", "technical_seo"],
        "system_prompt": (
            "You are an SEO Specialist. Perform keyword research, "
            "optimize content for search engines, analyze backlinks, "
            "and provide technical SEO recommendations."
        ),
    },
    AgentType.SOCIAL_SPECIALIST: {
        "name": "Social Media Specialist",
        "description": "Manages social media content and engagement",
        "capabilities": ["social_content", "engagement", "community"],
        "system_prompt": (
            "You are a Social Media Specialist. Create engaging social "
            "media content, manage community interactions, and develop "
            "social media strategies across platforms."
        ),
    },
    AgentType.COPYWRITER: {
        "name": "Copywriter",
        "description": "Writes persuasive marketing copy",
        "capabilities": ["copywriting", "headlines", "ad_copy"],
        "system_prompt": (
            "You are a Copywriter. Write compelling marketing copy, "
            "headlines, ad text, and persuasive content that drives "
            "action and conversion."
        ),
    },
    AgentType.DESIGNER: {
        "name": "Designer",
        "description": "Creates visual design concepts and guidelines",
        "capabilities": ["design", "visual_identity", "layout"],
        "system_prompt": (
            "You are a Designer. Create visual design concepts, "
            "brand guidelines, layout specifications, and creative "
            "briefs for marketing materials."
        ),
    },
    AgentType.BRAND_VOICE: {
        "name": "Brand Voice Specialist",
        "description": "Maintains brand voice consistency",
        "capabilities": ["brand_voice", "tone", "messaging"],
        "system_prompt": (
            "You are a Brand Voice Specialist. Ensure all content "
            "maintains consistent brand voice, tone, and messaging "
            "across all channels."
        ),
    },
    AgentType.CAMPAIGN_OPTIMIZER: {
        "name": "Campaign Optimizer",
        "description": "Optimizes ad campaigns for performance",
        "capabilities": ["campaign_optimization", "a_b_testing", "performance"],
        "system_prompt": (
            "You are a Campaign Optimizer. Analyze campaign performance, "
            "run A/B tests, optimize targeting, and maximize ROI."
        ),
    },
    AgentType.BID_MANAGER: {
        "name": "Bid Manager",
        "description": "Manages ad bidding strategies",
        "capabilities": ["bidding", "budget_allocation", "cost_optimization"],
        "system_prompt": (
            "You are a Bid Manager. Manage bidding strategies, "
            "allocate budgets, and optimize cost-per-click/acquisition."
        ),
    },
    AgentType.AUDIENCE_RESEARCHER: {
        "name": "Audience Researcher",
        "description": "Researches and segments target audiences",
        "capabilities": ["audience_research", "segmentation", "profiling"],
        "system_prompt": (
            "You are an Audience Researcher. Research target audiences, "
            "create buyer personas, segment audiences, and identify "
            "new targeting opportunities."
        ),
    },
    AgentType.MARKET_RESEARCHER: {
        "name": "Market Researcher",
        "description": "Conducts market analysis and research",
        "capabilities": ["market_research", "surveys", "analysis"],
        "system_prompt": (
            "You are a Market Researcher. Conduct market analysis, "
            "analyze industry trends, survey customer sentiment, "
            "and provide market intelligence."
        ),
    },
    AgentType.COMPETITOR_ANALYST: {
        "name": "Competitor Analyst",
        "description": "Analyzes competitor strategies",
        "capabilities": ["competitor_analysis", "benchmarking", "gap_analysis"],
        "system_prompt": (
            "You are a Competitor Analyst. Analyze competitor strategies, "
            "benchmark performance, identify gaps and opportunities."
        ),
    },
    AgentType.TREND_ANALYZER: {
        "name": "Trend Analyzer",
        "description": "Identifies and analyzes market trends",
        "capabilities": ["trend_analysis", "forecasting", "insights"],
        "system_prompt": (
            "You are a Trend Analyzer. Identify emerging trends, "
            "forecast market movements, and provide actionable insights."
        ),
    },
    AgentType.DATA_ANALYST: {
        "name": "Data Analyst",
        "description": "Analyzes data and generates insights",
        "capabilities": ["data_analysis", "visualization", "statistics"],
        "system_prompt": (
            "You are a Data Analyst. Analyze marketing data, create "
            "visualizations, perform statistical analysis, and generate "
            "actionable insights from data."
        ),
    },
    AgentType.ATTRIBUTION_MODELER: {
        "name": "Attribution Modeler",
        "description": "Models marketing attribution",
        "capabilities": ["attribution", "multi_touch", "roi_analysis"],
        "system_prompt": (
            "You are an Attribution Modeler. Build attribution models, "
            "analyze multi-touch attribution, and calculate channel ROI."
        ),
    },
    AgentType.REPORT_GENERATOR: {
        "name": "Report Generator",
        "description": "Creates marketing performance reports",
        "capabilities": ["reporting", "dashboards", "visualization"],
        "system_prompt": (
            "You are a Report Generator. Create comprehensive marketing "
            "performance reports, dashboards, and executive summaries."
        ),
    },
    AgentType.WORKFLOW_BUILDER: {
        "name": "Workflow Builder",
        "description": "Designs and builds automation workflows",
        "capabilities": ["workflow_design", "process_automation"],
        "system_prompt": (
            "You are a Workflow Builder. Design and build automated "
            "marketing workflows, triggers, and process automations."
        ),
    },
    AgentType.AUTOMATION_SCHEDULER: {
        "name": "Automation Scheduler",
        "description": "Schedules and manages automated tasks",
        "capabilities": ["scheduling", "automation", "timing"],
        "system_prompt": (
            "You are an Automation Scheduler. Schedule marketing tasks, "
            "manage automation timing, and optimize delivery schedules."
        ),
    },
    AgentType.INTEGRATION_MANAGER: {
        "name": "Integration Manager",
        "description": "Manages third-party integrations",
        "capabilities": ["integration", "api_management", "data_sync"],
        "system_prompt": (
            "You are an Integration Manager. Manage third-party "
            "integrations, API connections, and data synchronization."
        ),
    },
    AgentType.CONTENT_REVIEWER: {
        "name": "Content Reviewer",
        "description": "Reviews content for quality and compliance",
        "capabilities": ["content_review", "quality_assurance", "editing"],
        "system_prompt": (
            "You are a Content Reviewer. Review content for quality, "
            "brand consistency, legal compliance, and accuracy."
        ),
    },
    AgentType.PRIVACY_AUDITOR: {
        "name": "Privacy Auditor",
        "description": "Ensures privacy compliance",
        "capabilities": ["privacy", "gdpr", "data_protection"],
        "system_prompt": (
            "You are a Privacy Auditor. Ensure compliance with GDPR, "
            "CCPA, and other privacy regulations."
        ),
    },
    AgentType.POLICY_ENFORCER: {
        "name": "Policy Enforcer",
        "description": "Enforces organizational policies",
        "capabilities": ["policy", "compliance", "enforcement"],
        "system_prompt": (
            "You are a Policy Enforcer. Ensure all activities comply "
            "with organizational policies and industry standards."
        ),
    },
}


class SpecialistAgent(ReActAgent):
    """Specialist-level agent that executes concrete tasks.

    Specialists are leaf nodes in the hierarchy. They perform specific
    work using their domain expertise and available tools.
    """

    def __init__(
        self,
        agent_type: AgentType,
        config: AgentConfig | None = None,
        tenant_id: UUID | None = None,
        **kwargs: Any,
    ):
        if config is None:
            spec_config = SPECIALIST_CONFIGS.get(agent_type, {})
            config = AgentConfig(
                agent_type=agent_type,
                name=spec_config.get("name", agent_type.value),
                description=spec_config.get(
                    "description",
                    f"Specialist for {agent_type.value}",
                ),
                capabilities=spec_config.get("capabilities", []),
                autonomy_level=1,
                max_iterations=5,
                temperature=0.7,
                system_prompt=spec_config.get("system_prompt", ""),
            )
        if tenant_id:
            config.tenant_id = tenant_id
        super().__init__(config=config, tenant_id=tenant_id or uuid4(), **kwargs)

    def get_system_prompt(self) -> str:
        return self.config.system_prompt or (
            f"You are {self.config.name}, a specialist in "
            f"{', '.join(self.config.capabilities)}."
        )

    def prepare_input(self, input_data: Any) -> str:
        """Format the specialist's task."""
        if isinstance(input_data, dict):
            task = input_data.get("task", input_data)
            requirements = input_data.get("requirements", [])
            prompt = f"Task: {json.dumps(task, default=str)}"
            if requirements:
                prompt += f"\nRequirements: {json.dumps(requirements)}"
            return prompt
        return f"Task: {input_data}"
