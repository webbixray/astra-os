import logging
import re
from uuid import UUID

from app.application.ports.repositories import SystemPromptRepository
from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt

logger = logging.getLogger(__name__)


BUILTIN_PROMPTS: dict[str, dict] = {
    "system_chat": {
        "description": "Main ASTRA assistant system prompt for general chat",
        "category": PromptCategory.SYSTEM,
        "content": (
            "You are ASTRA, an AI-native marketing operating system assistant. "
            "You help users manage campaigns, create content, analyze performance, and automate marketing workflows.\n\n"
            "You have access to the following capabilities:\n"
            "- Campaign management: create, update, monitor campaigns\n"
            "- Content studio: create, review, publish content\n"
            "- Analytics: view performance metrics\n"
            "- Workflows: automate marketing processes\n\n"
            "For task-based requests (creating/updating campaigns or content, running analysis), "
            "your agent team will handle the execution.\n"
            "For general questions and conversation, respond directly.\n\n"
            "Response style: concise, actionable, professional. Use markdown for formatting."
        ),
        "variables": [],
    },
    "content_writer": {
        "description": "System prompt for AI content generation from templates",
        "category": PromptCategory.CONTENT,
        "content": (
            "You are a professional marketing content writer. "
            "Generate high-quality, engaging content following the template structure exactly.\n\n"
            "{{template_guidance}}\n\n"
            "Content type: {{content_type}}\n"
            "Sections to generate: {{sections}}\n\n"
            "{{brand_voice}}\n"
            "{{instructions}}\n\n"
            "Format your response with clear section headers matching the template sections. "
            "Use the format: ## section_name\ncontent"
        ),
        "variables": [
            "template_guidance",
            "content_type",
            "sections",
            "brand_voice",
            "instructions",
        ],
    },
    "content_rewriter": {
        "description": "System prompt for content rewriting",
        "category": PromptCategory.CONTENT,
        "content": (
            "You are a professional marketing content writer. "
            "Rewrite the following content according to the instructions. "
            "Preserve all key information and facts while improving style and impact.\n\n"
            "{{voice_context}}\n"
            "Additional instructions: {{instructions}}\n"
            "{{target_tone}}"
        ),
        "variables": ["voice_context", "instructions", "target_tone"],
    },
    "agent_ceo": {
        "description": "CEO agent system prompt for strategic planning",
        "category": PromptCategory.AGENT,
        "content": (
            "You are ASTRA-CEO, the chief executive agent. "
            "Your role is strategic planning, task delegation, cross-domain coordination, and escalation handling. "
            "You decompose complex user requests into clear tasks and assign them to the appropriate director agents."
        ),
        "variables": [],
    },
    "agent_campaign_director": {
        "description": "Campaign Director agent system prompt",
        "category": PromptCategory.AGENT,
        "content": (
            "You are the Campaign Director. "
            "Your expertise includes campaign creation, optimization, budget management, and channel strategy. "
            "You handle all marketing campaign-related tasks."
        ),
        "variables": [],
    },
    "agent_content_director": {
        "description": "Content Director agent system prompt",
        "category": PromptCategory.AGENT,
        "content": (
            "You are the Content Director. "
            "Your expertise includes content strategy, creation, brand voice, and content calendar management. "
            "You handle all content-related tasks."
        ),
        "variables": [],
    },
    "agent_analytics_director": {
        "description": "Analytics Director agent system prompt",
        "category": PromptCategory.AGENT,
        "content": (
            "You are the Analytics Director. "
            "Your expertise includes performance analysis, reporting, insight generation, and forecasting. "
            "You handle all analytics and reporting tasks."
        ),
        "variables": [],
    },
    "agent_workflow_director": {
        "description": "Workflow Director agent system prompt",
        "category": PromptCategory.AGENT,
        "content": (
            "You are the Workflow Director. "
            "Your expertise includes workflow design, automation, approval routing, and integration. "
            "You handle all workflow automation tasks."
        ),
        "variables": [],
    },
    "slash_commands": {
        "description": "Slash command help text for the ASTRA chat interface",
        "category": PromptCategory.TOOL,
        "content": (
            "Available commands:\n\n"
            "- **/campaign**: Create, update, or get details about campaigns\n"
            "- **/content**: Create or search content\n"
            "- **/analytics**: Get performance metrics\n"
            "- **/help**: List available slash commands"
        ),
        "variables": [],
    },
}


class PromptManager:
    def __init__(self, repository: SystemPromptRepository | None = None):
        self.repository = repository

    def set_repository(self, repository: SystemPromptRepository) -> None:
        self.repository = repository

    async def get_prompt(
        self,
        name: str,
        org_id: UUID | None = None,
        variables: dict[str, str] | None = None,
    ) -> str:
        content = None

        if self.repository:
            if org_id:
                org_prompt = await self.repository.find_by_name(name, org_id=org_id)
                if org_prompt and org_prompt.status == PromptStatus.ACTIVE:
                    content = org_prompt.content

            if content is None:
                global_prompt = await self.repository.find_by_name(name, org_id=None)
                if global_prompt and global_prompt.status == PromptStatus.ACTIVE:
                    content = global_prompt.content

        if content is None:
            builtin = BUILTIN_PROMPTS.get(name)
            if builtin is not None:
                content = builtin["content"]
            else:
                logger.warning("Prompt '%s' not found and no builtin default", name)
                return ""

        return self._render(content, variables or {})

    async def get_prompt_entity(
        self,
        name: str,
        org_id: UUID | None = None,
    ) -> SystemPrompt | None:
        if self.repository:
            if org_id:
                prompt = await self.repository.find_by_name(name, org_id=org_id)
                if prompt:
                    return prompt
            return await self.repository.find_by_name(name, org_id=None)
        return None

    async def save_prompt(self, prompt: SystemPrompt) -> SystemPrompt:
        if self.repository is None:
            raise RuntimeError("PromptManager has no repository configured")
        return await self.repository.save(prompt)

    async def seed_builtins(self) -> int:
        if self.repository is None:
            return 0
        seeded = 0
        for name, data in BUILTIN_PROMPTS.items():
            existing = await self.repository.find_by_name(name)
            if existing is None:
                prompt = SystemPrompt.create(
                    name=name,
                    content=data["content"],
                    description=data["description"],
                    category=data["category"],
                    variables=data.get("variables", []),
                    is_builtin=True,
                )
                await self.repository.save(prompt)
                seeded += 1
        if seeded:
            logger.info("Seeded %d builtin prompts", seeded)
        return seeded

    @staticmethod
    def _render(template: str, variables: dict[str, str]) -> str:
        def replace_var(match: re.Match) -> str:
            key = match.group(1).strip()
            return variables.get(key, match.group(0))

        return re.sub(r"\{\{(\w+)\}\}", replace_var, template)
