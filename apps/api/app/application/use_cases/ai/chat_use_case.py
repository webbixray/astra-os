from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from app.application.use_cases.ai.prompt_manager import PromptManager
from app.infrastructure.external_adapters.ai.router import AIRouter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.application.use_cases.agents.orchestrator import AgentOrchestrator
    from app.application.use_cases.knowledge.memory_service import MemoryService
    from app.domain.entities.ai.chat import ChatRequest
    from app.infrastructure.cache.redis import RedisCache

logger = logging.getLogger(__name__)

TASK_PATTERNS = [
    r"(create|make|new|start|launch)\s+(a\s+)?campaign",
    r"(create|make|write|generate)\s+(a\s+)?content",
    r"(create|make|new|write)\s+(a\s+)?(blog|post|social|email|ad)",
    r"(analyze|show|get|view)\s+(campaign|analytics|performance|metric|report)",
    r"(optimize|improve)\s+(campaign|content)",
    r"what('s| is) (the )?(status|performance) of",
]


def is_task_request(message: str) -> bool:
    msg_lower = message.lower()
    return any(re.search(p, msg_lower) for p in TASK_PATTERNS)


class ChatUseCase:
    def __init__(
        self,
        router: AIRouter | None = None,
        orchestrator: AgentOrchestrator | None = None,
        memory_service: MemoryService | None = None,
        prompt_manager: PromptManager | None = None,
        cache: RedisCache | None = None,
    ):
        self.router = router or AIRouter()
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.prompt_manager = prompt_manager or PromptManager()
        self.cache = cache

    def set_orchestrator(self, orchestrator: AgentOrchestrator) -> None:
        self.orchestrator = orchestrator

    def set_memory_service(self, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    def set_prompt_manager(self, prompt_manager: PromptManager) -> None:
        self.prompt_manager = prompt_manager

    async def _build_system_prompt(self, page_context: dict, memory_notes: str = "") -> str:
        try:
            prompt = await self.prompt_manager.get_prompt("system_chat")
        except Exception as e:
            logger.warning("Failed to get system_chat prompt: %s", e)
            prompt = ""
        if page_context.get("page"):
            prompt += f"\n\nCurrent page: {page_context['page']}"
        if page_context.get("campaign"):
            prompt += f"\n\nCampaign context: {page_context['campaign']}"
        if page_context.get("content"):
            prompt += f"\n\nContent context: {page_context['content']}"
        if memory_notes:
            prompt += f"\n\nRelevant memories:\n{memory_notes}"
        return prompt

    async def _handle_slash_command(self, message: str) -> str | None:
        if not message.startswith("/"):
            return None
        cmd = message.split(maxsplit=1)[0].lower()
        if cmd == "/help" or cmd not in ("/campaign", "/content", "/analytics"):
            try:
                return await self.prompt_manager.get_prompt("slash_commands")
            except Exception as e:
                logger.warning("Failed to get slash_commands prompt: %s", e)
                return "Available commands: /campaign, /content, /analytics, /help"
        return None

    async def _get_memory_context(self, organization_id: str, user_id: str, message: str) -> str:
        if not self.memory_service:
            return ""
        try:
            memories = await self.memory_service.recall(
                organization_id=organization_id,
                user_id=user_id,
                query=message,
                limit=3,
            )
            if memories:
                return "\n".join(f"- {m['key']}: {m['value'][:200]}" for m in memories)
        except Exception as e:
            logger.warning("Failed to get memory context: %s", e)
        return ""

    async def _capture_memory(
        self,
        organization_id: str,
        user_id: str,
        message: str,
        response: str,
    ) -> None:
        if not self.memory_service:
            return
        try:
            await self.memory_service.capture_conversation(
                organization_id=organization_id,
                user_id=user_id,
                message=message,
                response=response,
            )
        except Exception as e:
            logger.warning("Failed to capture memory: %s", e)

    def _build_messages(self, system_prompt: str, request: ChatRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(msg.to_dict() for msg in request.messages)
        messages.append({"role": "user", "content": request.message})
        return messages

    async def _process_via_agents(
        self,
        request: ChatRequest,
    ) -> str | None:
        if not self.orchestrator or not is_task_request(request.message):
            return None
        try:
            result = await self.orchestrator.process_user_request(
                user_id=request.user_id,
                organization_id=request.organization_id,
                message=request.message,
            )
            agent_info = (
                f"🤖 Agents: {', '.join(result['agents_involved'])}\n\n"
                if result["agents_involved"]
                else ""
            )
            return f"{agent_info}{result['response']}"
        except Exception:
            logger.exception("Failed to process task request: %s")
            return None

    async def _get_cached_response(self, cache_key: str) -> str | None:
        if not self.cache:
            return None
        try:
            return await self.cache.get(cache_key)
        except Exception as e:
            logger.debug("Cache get failed: %s", e)
            return None

    async def _set_cached_response(self, cache_key: str, response: str, ttl: int = 300) -> None:
        if not self.cache:
            return
        try:
            await self.cache.set(cache_key, response, ttl=ttl)
        except Exception as e:
            logger.debug("Cache set failed: %s", e)

    async def stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        slash_response = await self._handle_slash_command(request.message)
        if slash_response:
            for char in slash_response:
                yield char
            return

        agent_response = await self._process_via_agents(request)
        if agent_response:
            for char in agent_response:
                yield char
            await self._capture_memory(
                organization_id=request.organization_id,
                user_id=request.user_id,
                message=request.message,
                response=agent_response,
            )
            return

        cache_key = f"chat:{request.organization_id}:{hash(request.message)}"
        cached = await self._get_cached_response(cache_key)
        if cached:
            for char in cached:
                yield char
            return

        memory_notes = await self._get_memory_context(
            organization_id=request.organization_id,
            user_id=request.user_id,
            message=request.message,
        )

        system_prompt = await self._build_system_prompt(request.page_context, memory_notes)
        messages = self._build_messages(system_prompt, request)

        full_response = ""
        async for chunk in self.router.stream_chat(messages):
            full_response += chunk
            yield chunk

        if full_response:
            await self._capture_memory(
                organization_id=request.organization_id,
                user_id=request.user_id,
                message=request.message,
                response=full_response,
            )
            await self._set_cached_response(cache_key, full_response)

    async def execute(
        self,
        request: ChatRequest,
    ) -> str:
        slash_response = await self._handle_slash_command(request.message)
        if slash_response:
            return slash_response

        agent_response = await self._process_via_agents(request)
        if agent_response:
            await self._capture_memory(
                organization_id=request.organization_id,
                user_id=request.user_id,
                message=request.message,
                response=agent_response,
            )
            return agent_response

        cache_key = f"chat:{request.organization_id}:{hash(request.message)}"
        cached = await self._get_cached_response(cache_key)
        if cached:
            return cached

        memory_notes = await self._get_memory_context(
            organization_id=request.organization_id,
            user_id=request.user_id,
            message=request.message,
        )

        system_prompt = await self._build_system_prompt(request.page_context, memory_notes)
        messages = self._build_messages(system_prompt, request)

        response = await self.router.chat(messages)

        await self._capture_memory(
            organization_id=request.organization_id,
            user_id=request.user_id,
            message=request.message,
            response=response,
        )
        await self._set_cached_response(cache_key, response)

        return response


# Backward-compatible module-level wrappers for tests
def build_system_prompt(page_context: dict, memory_notes: str = "") -> str:
    import asyncio

    use_case = object.__new__(ChatUseCase)
    use_case.prompt_manager = None
    use_case.memory_service = None
    use_case.router = None
    use_case.cache = None
    return asyncio.run(use_case._build_system_prompt(page_context, memory_notes))


def handle_slash_command(message: str) -> str | None:
    import asyncio

    use_case = object.__new__(ChatUseCase)
    use_case.prompt_manager = None
    return asyncio.run(use_case._handle_slash_command(message))
