from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

import httpx

from app.application.ports.ai_provider import AIProvider
from app.config import config

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

MODEL_COSTS_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "meta/llama-3.1-70b-instruct": {"input": 0.001, "output": 0.001},
    "meta/llama-3.1-8b-instruct": {"input": 0.0002, "output": 0.0002},
}

NVIDIA_NIM_CHAT_URL = (
    f"{config.nvidia_nim_base_url}/chat/completions" if config.nvidia_nim_base_url else ""
)
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_CHAT_URL = "https://api.anthropic.com/v1/messages"
GEMINI_CHAT_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass
class UsageRecord:
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0
    estimated_cost: float = 0.0
    error: str | None = None
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.estimated_cost == 0.0 and (self.input_tokens or self.output_tokens):
            self.estimated_cost = _estimate_cost(self.model, self.input_tokens, self.output_tokens)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class AIProviderError(Exception):
    def __init__(self, provider: str, model: str, status_code: int, message: str) -> None:
        self.provider = provider
        self.model = model
        self.status_code = status_code
        super().__init__(f"{provider}/{model} error {status_code}: {message}")


class UsageTracker:
    _records: ClassVar[list[UsageRecord]] = []
    _max_records: ClassVar[int] = 10000

    @classmethod
    def record(cls, record: UsageRecord) -> None:
        cls._records.append(record)
        if len(cls._records) > cls._max_records:
            cls._records = cls._records[-cls._max_records :]
        logger.info(
            "AI call: %s/%s (%d+%d tokens, $%.5f, %.0fms)",
            record.provider,
            record.model,
            record.input_tokens,
            record.output_tokens,
            record.estimated_cost,
            record.duration_ms,
        )

    @classmethod
    def get_recent(cls, limit: int = 100) -> list[UsageRecord]:
        return cls._records[-limit:]

    @classmethod
    def get_cost_summary(cls) -> dict:
        total_cost = sum(r.estimated_cost for r in cls._records)
        total_tokens = sum(r.total_tokens for r in cls._records)
        return {
            "total_cost": round(total_cost, 6),
            "total_calls": len(cls._records),
            "total_tokens": total_tokens,
            "errors": sum(1 for r in cls._records if r.error),
        }


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS_PER_1K_TOKENS.get(model, {"input": 0.001, "output": 0.002})
    return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


async def _stream_sse(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    json_data: dict[str, Any],
) -> AsyncIterator[str]:
    async with client.stream("POST", url, headers=headers, json=json_data) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue


async def _stream_sse_anthropic(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    json_data: dict[str, Any],
) -> AsyncIterator[str]:
    async with client.stream("POST", url, headers=headers, json=json_data) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                try:
                    chunk = json.loads(data)
                    if chunk.get("type") == "content_block_delta":
                        delta = chunk.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    continue


async def _stream_sse_gemini(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    json_data: dict[str, Any],
) -> AsyncIterator[str]:
    async with client.stream("POST", url, headers=headers, json=json_data) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                try:
                    chunk = json.loads(data)
                    candidates = chunk.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                except json.JSONDecodeError:
                    continue


class NvidiaNIMProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = ""
        self.base_url = config.nvidia_nim_base_url
        self.default_model = "meta/llama-3.1-70b-instruct"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not self.base_url or not self.api_key:
            return
        model_name = model or self.default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            async for content in _stream_sse(
                client,
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json_data={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                },
            ):
                yield content

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not self.base_url or not self.api_key:
            return ""
        model_name = model or self.default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = config.openai_api_key
        self.default_model = "gpt-4o-mini"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            return
        model_name = model or self.default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            async for content in _stream_sse(
                client,
                OPENAI_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json_data={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                },
            ):
                yield content

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            return ""
        model_name = model or self.default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENAI_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class AnthropicProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = config.anthropic_api_key
        self.default_model = "claude-3-sonnet-20240229"

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        system = ""
        converted = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                converted.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )
        return system, converted

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            return
        model_name = model or self.default_model
        system, converted_messages = self._convert_messages(messages)
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": converted_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120.0) as client:
            async for content in _stream_sse_anthropic(
                client,
                ANTHROPIC_CHAT_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json_data=payload,
            ):
                yield content

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            return ""
        model_name = model or self.default_model
        system, converted_messages = self._convert_messages(messages)
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": converted_messages,
            "max_tokens": 4096,
            "stream": False,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                ANTHROPIC_CHAT_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content_blocks = data.get("content", [])
            return "".join(block.get("text", "") for block in content_blocks)


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = config.gemini_api_key
        self.default_model = "gemini-1.5-pro"

    def _convert_messages(self, messages: list[dict]) -> dict[str, Any]:
        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append(
                    {
                        "role": gemini_role,
                        "parts": [{"text": content}],
                    }
                )
        result: dict[str, Any] = {"contents": contents}
        if system_instruction:
            result["systemInstruction"] = system_instruction
        return result

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            return
        model_name = model or self.default_model
        payload = self._convert_messages(messages)
        payload["generationConfig"] = {"maxOutputTokens": 4096}
        url = f"{GEMINI_CHAT_URL}/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            async for content in _stream_sse_gemini(
                client,
                url,
                headers={"Content-Type": "application/json"},
                json_data=payload,
            ):
                yield content

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            return ""
        model_name = model or self.default_model
        payload = self._convert_messages(messages)
        payload["generationConfig"] = {"maxOutputTokens": 4096}
        url = f"{GEMINI_CHAT_URL}/{model_name}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                return "".join(part.get("text", "") for part in parts)
            return ""


class AIRouter:
    def __init__(self) -> None:
        self.providers: list[AIProvider] = []
        if config.nvidia_nim_base_url:
            self.providers.append(NvidiaNIMProvider())
        if config.openai_api_key:
            self.providers.append(OpenAIProvider())
        if config.anthropic_api_key:
            self.providers.append(AnthropicProvider())
        if config.gemini_api_key:
            self.providers.append(GeminiProvider())

    def _get_provider_name(self, provider: AIProvider) -> str:
        if isinstance(provider, NvidiaNIMProvider):
            return "nvidia_nim"
        if isinstance(provider, OpenAIProvider):
            return "openai"
        if isinstance(provider, AnthropicProvider):
            return "anthropic"
        if isinstance(provider, GeminiProvider):
            return "gemini"
        return type(provider).__name__.lower()

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        for provider in self.providers:
            start = time.monotonic()
            provider_name = self._get_provider_name(provider)
            try:
                full_response = ""
                async for chunk in provider.stream_chat(messages, model=model):
                    full_response += chunk
                    yield chunk
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                    )
                )
            except httpx.HTTPStatusError as e:
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                        error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                    )
                )
                logger.warning("AI provider %s failed: %s", provider_name, e)
                continue
            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                        error=str(e),
                    )
                )
                logger.warning("AI provider %s failed: %s", provider_name, e)
                continue

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        for provider in self.providers:
            start = time.monotonic()
            provider_name = self._get_provider_name(provider)
            try:
                result = await provider.chat(messages, model=model)
            except httpx.HTTPStatusError as e:
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                        error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                    )
                )
                logger.warning("AI provider %s failed: %s", provider_name, e)
                continue
            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                        error=str(e),
                    )
                )
                logger.warning("AI provider %s failed: %s", provider_name, e)
                continue
            else:
                duration_ms = (time.monotonic() - start) * 1000
                UsageTracker.record(
                    UsageRecord(
                        provider=provider_name,
                        model=model or getattr(provider, "default_model", "unknown"),
                        duration_ms=duration_ms,
                    )
                )
                return result
        return "I'm sorry, I'm having trouble connecting to my AI services right now."
