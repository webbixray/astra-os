from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from app.application.use_cases.agents.tool_registry import ToolCategory, ToolRegistry
from app.domain.entities.agents.agent import Agent, AgentRole, AgentStatus
from app.domain.entities.agents.communication import (
    MessageBus,
)
from app.domain.entities.agents.task import AgentTask

if TYPE_CHECKING:
    from uuid import UUID

    from app.infrastructure.external_adapters.ai.router import AIRouter

logger = logging.getLogger(__name__)

PRESET_AGENTS: list[dict] = [
    {
        "name": "ASTRA-CEO",
        "role": AgentRole.CEO,
        "capabilities": [
            "strategic planning",
            "task delegation",
            "cross-domain coordination",
            "escalation handling",
        ],
    },
    {
        "name": "Campaign Director",
        "role": AgentRole.CAMPAIGN_DIRECTOR,
        "capabilities": [
            "campaign creation",
            "campaign optimization",
            "budget management",
            "channel strategy",
        ],
    },
    {
        "name": "Content Director",
        "role": AgentRole.CONTENT_DIRECTOR,
        "capabilities": [
            "content strategy",
            "content creation",
            "brand voice",
            "content calendar",
        ],
    },
    {
        "name": "Analytics Director",
        "role": AgentRole.ANALYTICS_DIRECTOR,
        "capabilities": [
            "performance analysis",
            "reporting",
            "insight generation",
            "forecasting",
        ],
    },
    {
        "name": "Workflow Director",
        "role": AgentRole.WORKFLOW_DIRECTOR,
        "capabilities": [
            "workflow design",
            "automation",
            "approval routing",
            "integration",
        ],
    },
]

DIRECTOR_TO_CATEGORY = {
    "Campaign Director": ToolCategory.CAMPAIGN,
    "Content Director": ToolCategory.CONTENT,
    "Analytics Director": ToolCategory.ANALYTICS,
    "Workflow Director": ToolCategory.WORKFLOW,
}

CLASSIFICATION_PROMPT = """You are an AI agent orchestrator for a marketing platform. Classify the following user request into the most appropriate director agent and a list of specific subtasks.

Available directors:
- campaign_director: Handles campaign creation, optimization, budget, channels
- content_director: Handles content strategy, writing, brand voice
- analytics_director: Handles performance analysis, reporting, metrics
- workflow_director: Handles workflow design, automation, approval routing
- general: Anything that doesn't fit the above

User request: {message}

Return ONLY valid JSON with no extra text, no markdown, no code fences:
{{"director": "campaign_director|content_director|analytics_director|workflow_director|general", "subtasks": [{{"title": "...", "description": "..."}}]}}"""


class AgentOrchestrator:
    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        message_bus: MessageBus | None = None,
        ai_router: AIRouter | None = None,
    ) -> None:
        self.tool_registry = tool_registry or ToolRegistry()
        self.message_bus = message_bus or MessageBus()
        self.ai_router = ai_router
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, AgentTask] = {}
        self._init_preset_agents()

    async def get_director_for_task(self, task: AgentTask) -> Agent:
        classification = await self._classify_intent(task.description or task.title)
        return self._resolve_director(classification["director"])

    def _decompose_task(self, task: AgentTask, director_name: str) -> list[AgentTask]:
        name_to_key = {
            "Campaign Director": "campaign_director",
            "Content Director": "content_director",
            "Analytics Director": "analytics_director",
            "Workflow Director": "workflow_director",
        }
        director_key = name_to_key.get(director_name, "general")
        message = task.description or task.title
        subtask_defs = self._generate_subtasks(director_key, message)
        return [
            AgentTask.create(
                title=st["title"],
                description=st.get("description", message),
                assigned_by=task.assigned_by or task.id,
                parent_task_id=task.id,
            )
            for st in subtask_defs
        ]

    def _generate_subtasks(self, director: str, message: str) -> list[dict]:
        msg_lower = message.lower()
        subtasks = []
        if director == "campaign_director":
            if "create" in msg_lower or "new" in msg_lower:
                subtasks.append({"title": "Generate campaign suggestions", "description": message})
            if "optimize" in msg_lower or "improve" in msg_lower:
                subtasks.append(
                    {
                        "title": "Analyze campaign performance",
                        "description": f"Find optimization opportunities: {message}",
                    }
                )
        elif director == "content_director":
            if "create" in msg_lower or "write" in msg_lower:
                subtasks.append(
                    {
                        "title": "Generate content outline",
                        "description": f"Create outline for: {message}",
                    }
                )
            if "review" in msg_lower:
                subtasks.append(
                    {
                        "title": "Review content quality",
                        "description": f"Review and provide feedback: {message}",
                    }
                )
        elif director == "analytics_director":
            subtasks.append(
                {"title": "Gather performance data", "description": f"Analyze: {message}"}
            )
        if not subtasks:
            subtasks.append({"title": "Process request", "description": message})
        return subtasks

    def set_ai_router(self, ai_router: AIRouter) -> None:
        self.ai_router = ai_router

    def _init_preset_agents(self) -> None:
        for cfg in PRESET_AGENTS:
            agent = Agent.create(
                name=cfg["name"],
                role=cfg["role"],
                capabilities=cfg["capabilities"],
            )
            self.agents[cfg["name"]] = agent

    def get_ceo(self) -> Agent:
        return self.agents["ASTRA-CEO"]

    async def _classify_intent(self, message: str) -> dict:
        prompt = CLASSIFICATION_PROMPT.format(message=message[:500])
        try:
            if self.ai_router:
                response = await self.ai_router.chat(
                    [
                        {"role": "user", "content": prompt},
                    ]
                )
                clean = response.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[-1].rsplit("\n", 1)[0]
                    clean = clean.removesuffix("```")
                result = json.loads(clean)
                return {
                    "director": result.get("director", "general"),
                    "subtasks": result.get("subtasks", []),
                }
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("AI intent classification failed: %s", e)

        return self._fallback_classify(message)

    def _fallback_classify(self, message: str) -> dict:
        msg_lower = message.lower()
        director_map = [
            (["campaign", "campaigns"], "campaign_director"),
            (["content", "blog", "social", "email", "write", "create content"], "content_director"),
            (
                ["analytics", "report", "metric", "performance", "analyze", "show"],
                "analytics_director",
            ),
            (["workflow", "automation", "approval", "workflows"], "workflow_director"),
        ]
        director = "general"
        for keywords, dir_name in director_map:
            if any(kw in msg_lower for kw in keywords):
                director = dir_name
                break

        subtasks = self._generate_subtasks(director, message)

        return {"director": director, "subtasks": subtasks}

    def _resolve_director(self, director_key: str) -> Agent:
        name_map = {
            "campaign_director": "Campaign Director",
            "content_director": "Content Director",
            "analytics_director": "Analytics Director",
            "workflow_director": "Workflow Director",
        }
        agent_name = name_map.get(director_key)
        if agent_name and agent_name in self.agents:
            return self.agents[agent_name]
        return self.agents.get("Campaign Director", next(iter(self.agents.values())))

    async def process_user_request(
        self,
        user_id: UUID,
        organization_id: UUID,
        message: str,
    ) -> dict:
        ceo = self.get_ceo()
        ceo.set_status(AgentStatus.PROCESSING)

        task = AgentTask.create(
            title=f"Process user request: {message[:50]}",
            description=message,
            assigned_by=user_id,
        )
        self.tasks[str(task.id)] = task

        try:
            result = await self._route_task(task, organization_id)
            ceo.set_status(AgentStatus.IDLE)
            task.complete(result)
            return {
                "task_id": str(task.id),
                "response": result.get("response", ""),
                "agents_involved": result.get("agents_involved", []),
                "status": "completed",
            }
        except Exception as e:
            ceo.set_status(AgentStatus.ERROR)
            task.fail(str(e))
            return {
                "task_id": str(task.id),
                "response": f"I encountered an error processing your request: {e}",
                "agents_involved": [],
                "status": "failed",
            }

    async def _route_task(
        self,
        task: AgentTask,
        organization_id: UUID,
    ) -> dict:
        director = await self.get_director_for_task(task)
        director.set_status(AgentStatus.PROCESSING)
        task.assign(director.id)

        tool_category = DIRECTOR_TO_CATEGORY.get(director.name, ToolCategory.COMMUNICATION)

        subtasks = self._decompose_task(task, director.name)

        results = await asyncio.gather(
            *[
                self._execute_subtask(subtask, tool_category, organization_id)
                for subtask in subtasks
            ],
            return_exceptions=True,
        )

        processed = []
        for r in results:
            if isinstance(r, Exception):
                processed.append({"tool": "default", "error": str(r)})
            else:
                processed.append(r)

        director.set_status(AgentStatus.IDLE)

        return {
            "response": self._consolidate_results(processed),
            "agents_involved": [director.name],
            "subtask_results": processed,
        }

    async def _execute_subtask(
        self,
        subtask: AgentTask,
        category: ToolCategory,
        organization_id: UUID,
    ) -> dict:
        subtask.start()
        tools = self.tool_registry.list_by_category(category)

        best_tool = None
        best_score = 0

        for tool in tools:
            score = 0
            name_keywords = tool.name.lower().split("_")
            desc_keywords = tool.description.lower().split()
            subj_title = subtask.title.lower()
            subj_desc = (subtask.description or "").lower()

            for kw in name_keywords:
                if kw in subj_title or kw in subj_desc:
                    score += 2

            for kw in desc_keywords:
                if len(kw) > 3 and (kw in subj_title or kw in subj_desc):
                    score += 1

            if score > best_score:
                best_score = score
                best_tool = tool

        if best_tool and best_score > 0:
            try:
                result = await best_tool.execute(
                    organization_id=str(organization_id),
                    query=subtask.description,
                )
            except Exception as e:
                subtask.fail(str(e))
                return {"tool": best_tool.name, "error": str(e)}
            else:
                subtask.complete(result)
                return {"tool": best_tool.name, "result": result}

        subtask.complete({"note": "No specific tool matched. Request logged."})
        return {
            "tool": "default",
            "result": f"I've noted your request about: {subtask.description}",
        }

    def _consolidate_results(self, results: list[dict]) -> str:
        parts = []
        for r in results:
            if "result" in r:
                if isinstance(r["result"], dict):
                    if "response" in r["result"]:
                        parts.append(r["result"]["response"])
                    elif "error" in r["result"]:
                        parts.append(f"Issue: {r['result']['error']}")
                    else:
                        parts.append(str(r["result"]))
                else:
                    parts.append(str(r["result"]))
            if "error" in r:
                parts.append(f"Note: {r['error']}")

        return "\n\n".join(parts) if parts else "I've processed your request."
