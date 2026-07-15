from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

import httpx

# Circuit breaker integration
from services.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    get_circuit_breaker_registry,
)

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


class NvidiaNIMProvider:
    def __init__(self) -> None:
        self.default_model = "meta/llama-3.1-70b-instruct"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not config.nvidia_nim_base_url:
            return
            yield

        url = NVIDIA_NIM_CHAT_URL
        headers = {
            "Authorization": f"Bearer {config.nvidia_nim_api_key}",
            "Content-Type": "application/json",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async for chunk in _stream_sse(client, url, headers, json_data):
                yield chunk

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not config.nvidia_nim_base_url:
            return ""

        url = NVIDIA_NIM_CHAT_URL
        headers = {
            "Authorization": f"Bearer {config.nvidia_nim_api_key}",
            "Content-Type": "application/json",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class OpenAIProvider:
    def __init__(self) -> None:
        self.default_model = "gpt-4o"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not config.openai_api_key:
            return
            yield

        url = OPENAI_CHAT_URL
        headers = {
            "Authorization": f"Bearer {config.openai_api_key}",
            "Content-Type": "application/json",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async for chunk in _stream_sse(client, url, headers, json_data):
                yield chunk

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not config.openai_api_key:
            return ""

        url = OPENAI_CHAT_URL
        headers = {
            "Authorization": f"Bearer {config.openai_api_key}",
            "Content-Type": "application/json",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class AnthropicProvider:
    def __init__(self) -> None:
        self.default_model = "claude-3-sonnet-20240229"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not config.anthropic_api_key:
            return
            yield

        url = ANTHROPIC_CHAT_URL
        headers = {
            "x-api-key": config.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": True,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async for chunk in _stream_sse(client, url, headers, json_data):
                yield chunk

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not config.anthropic_api_key:
            raise RuntimeError("Anthropic not configured")

        url = ANTHROPIC_CHAT_URL
        headers = {
            "x-api-key": config.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        json_data = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": False,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


class GeminiProvider:
    def __init__(self) -> None:
        self.default_model = "gemini-1.5-pro"

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        if not config.gemini_api_key:
            return
            yield

        url = f"{GEMINI_CHAT_URL}/{model or self.default_model}:streamGenerateContent"
        params = {"key": config.gemini_api_key}
        headers = {"Content-Type": "application/json"}

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        json_data = {
            "contents": contents,
            "generationConfig": {"temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=60.0) as client, client.stream(
            "POST", url, params=params, headers=headers, json=json_data
        ) as response:
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
                                if "text" in part:
                                    yield part["text"]
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        if not config.gemini_api_key:
            raise RuntimeError("Gemini not configured")

        url = f"{GEMINI_CHAT_URL}/{model or self.default_model}:generateContent"
        params = {"key": config.gemini_api_key}
        headers = {"Content-Type": "application/json"}

        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        json_data = {
            "contents": contents,
            "generationConfig": {"temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, params=params, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


class AIRouter:
    def __init__(self) -> None:
        self.providers: list[AIProvider] = []
        self._provider_names: list[str] = []
        if config.nvidia_nim_base_url:
            self.providers.append(NvidiaNIMProvider())
            self._provider_names.append("nvidia_nim")
        if config.openai_api_key:
            self.providers.append(OpenAIProvider())
            self._provider_names.append("openai")
        if config.anthropic_api_key:
            self.providers.append(AnthropicProvider())
            self._provider_names.append("anthropic")
        if config.gemini_api_key:
            self.providers.append(GeminiProvider())
            self._provider_names.append("gemini")

        # Initialize circuit breakers for each provider
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        registry = get_circuit_breaker_registry()
        for name in self._provider_names:
            cb_config = CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=30.0,
                exclude_exceptions=(httpx.TimeoutException,),
            )
            self._circuit_breakers[name] = registry.get_or_create(name, cb_config)

    def _get_provider_name(self, provider: AIProvider) -> str:
        if isinstance(provider, NvidiaNIMProvider):
            return "nvidia_nim"
        if isinstance(provider, OpenAIProvider):
            return "openai"
        if isinstance(provider, AnthropicProvider):
            return "anthropic"
        if isinstance(provider, GeminiProvider):
            return "gemini"
        return "unknown"

    async def _call_with_circuit_breaker(
            self,
            provider: AIProvider,
            method: str,
            *args,
            **kwargs
        ) -> Any:
            """Execute a provider method with circuit breaker protection."""
            provider_name = self._get_provider_name(provider)
            circuit_breaker = self._circuit_breakers.get(provider_name)

            # stream_chat returns an async generator, circuit breaker not compatible
            # Skip circuit breaker for streaming methods
            if method == "stream_chat":
                func = getattr(provider, method)
                return func(*args, **kwargs)

            if circuit_breaker is None:
                # No circuit breaker, call directly
                func = getattr(provider, method)
                return await func(*args, **kwargs)

            async def _call():
                func = getattr(provider, method)
                return await func(*args, **kwargs)

            try:
                return await circuit_breaker.call(_call)
            except CircuitOpenError as e:
                logger.warning("Circuit open for %s, skipping provider: %s", provider_name, e)
                raise  # Re-raise to trigger fallback

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
                # For streaming, bypass circuit breaker and call provider directly
                stream_result = provider.stream_chat(messages, model=model)
                async for chunk in stream_result:
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
            except CircuitOpenError:
                logger.warning("Circuit open for %s, skipping provider", provider_name)
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
                result = await self._call_with_circuit_breaker(
                    provider, "chat", messages, model=model
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
            except CircuitOpenError:
                logger.warning("Circuit open for %s, skipping provider", provider_name)
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
