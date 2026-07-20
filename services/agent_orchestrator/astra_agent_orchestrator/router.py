"""Model Router with multi-provider fallback chain."""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""

    NVIDIA_NIM = "nvidia_nim"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    VLLM = "vllm"


class ModelCapability(str, Enum):
    """Model capabilities."""

    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE = "code"
    REASONING = "reasoning"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    provider: ModelProvider
    model_name: str
    display_name: str
    capabilities: list[ModelCapability]
    max_tokens: int
    context_window: int
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    timeout_seconds: int = 60
    max_retries: int = 3
    base_url: str | None = None
    api_key_env: str | None = None
    priority: int = 0  # Lower = higher priority
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelRequest(BaseModel):
    """Request to generate a response from a model."""

    messages: list[dict[str, str]] = Field(default_factory=list)
    prompt: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    top_k: int | None = None
    stop: list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | None = None
    response_format: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Response from a model."""

    model_id: str
    content: str
    finish_reason: str = "stop"
    usage: dict[str, int] = Field(
        default_factory=dict
    )  # prompt_tokens, completion_tokens, total_tokens
    latency_ms: int = 0
    cost_usd: float = 0.0
    model_name: str
    provider: ModelProvider
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: UUID = Field(default_factory=uuid4)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamingChunk(BaseModel):
    """A chunk of streaming response."""

    content: str
    finish_reason: str | None = None
    delta: dict[str, Any] = Field(default_factory=dict)


class ModelProviderBase(ABC):
    """Abstract base class for model providers."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model."""

    @abstractmethod
    async def stream_generate(self, request: ModelRequest):
        """Generate a streaming response from the model."""

    @abstractmethod
    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings for texts."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            timeout = httpx.Timeout(self.config.timeout_seconds)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        client = self._get_client()
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                start = time.time()
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                )
                latency = time.time() - start
                self._total_latency += latency
                self._request_count += 1

                if response.is_success:
                    return response
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = (2**attempt) + 0.1
                    logger.warning(
                        "Rate limited by %s, waiting %.1fs (attempt %d/%d)",
                        self.config.provider.value,
                        wait_time,
                        attempt + 1,
                        self.config.max_retries + 1,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                # Other error
                error_text = response.text
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text}",
                    request=response.request,
                    response=response,
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self.config.max_retries:
                    wait_time = (2**attempt) + 0.1
                    logger.warning(
                        "Request to %s failed: %s, retrying in %.1fs",
                        self.config.provider.value,
                        e,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

        # All retries exhausted
        self._error_count += 1
        raise last_error or RuntimeError("Max retries exceeded")

    def get_stats(self) -> dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model_name,
            "requests": self._request_count,
            "errors": self._error_count,
            "avg_latency_ms": (
                self._total_latency / self._request_count * 1000 if self._request_count > 0 else 0
            ),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class NVIDIANIMProvider(ModelProviderBase):
    """NVIDIA NIM provider (primary)."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://integrate.api.nvidia.com/v1"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        api_key = self.config.metadata.get("api_key", "") or os.environ.get(
            "NVIDIA_NIM_API_KEY", ""
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = self._format_messages(request)
        payload = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stop": request.stop,
            "stream": request.stream,
        }

        if request.tools:
            payload["tools"] = request.tools
            payload["tool_choice"] = request.tool_choice or "auto"

        if request.response_format:
            payload["response_format"] = request.response_format

        start = time.time()
        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json_data=payload,
        )
        latency_ms = int((time.time() - start) * 1000)

        data = response.json()
        choice = data["choices"][0]

        return ModelResponse(
            model_id=data.get("id", str(uuid4())),
            content=choice["message"]["content"],
            finish_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
            latency_ms=latency_ms,
            cost_usd=self._calculate_cost(data.get("usage", {})),
            model_name=self.config.model_name,
            provider=ModelProvider.NVIDIA_NIM,
        )

    async def stream_generate(self, request: ModelRequest):
        api_key = self.config.metadata.get("api_key", "") or os.environ.get(
            "NVIDIA_NIM_API_KEY", ""
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        messages = self._format_messages(request)
        payload = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stream": True,
        }

        if request.tools:
            payload["tools"] = request.tools

        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if data.get("choices"):
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield StreamingChunk(
                                    content=delta["content"],
                                    finish_reason=data["choices"][0].get("finish_reason"),
                                )
                    except json.JSONDecodeError:
                        continue

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        api_key = self.config.metadata.get("api_key", "") or os.environ.get(
            "NVIDIA_NIM_API_KEY", ""
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model or "nvidia/embedding-3-large",
            "input": texts,
        }

        response = await self._make_request(
            "POST",
            f"{self.base_url}/embeddings",
            headers=headers,
            json_data=payload,
        )

        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def health_check(self) -> bool:
        try:
            api_key = self.config.metadata.get("api_key", "") or os.environ.get(
                "NVIDIA_NIM_API_KEY", ""
            )
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await self._make_request("GET", f"{self.base_url}/models", headers)
            return response.is_success
        except Exception:
            return False

    def _format_messages(self, request: ModelRequest) -> list[dict[str, str]]:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        messages.extend(request.messages)
        return messages

    def _calculate_cost(self, usage: dict[str, int]) -> float:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return (
            prompt_tokens * self.config.cost_per_1k_input
            + completion_tokens * self.config.cost_per_1k_output
        ) / 1000


class OpenAIProvider(ModelProviderBase):
    """OpenAI provider (fallback)."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        api_key = self.config.metadata.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = self._format_messages(request)
        payload = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stop": request.stop,
            "stream": request.stream,
        }

        if request.tools:
            payload["tools"] = request.tools
            payload["tool_choice"] = request.tool_choice or "auto"

        if request.response_format:
            payload["response_format"] = request.response_format

        start = time.time()
        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.metadata.get('api_key', '')}",
                "Content-Type": "application/json",
            },
            json_data=payload,
        )
        latency_ms = int((time.time() - start) * 1000)

        data = response.json()
        choice = data["choices"][0]

        return ModelResponse(
            model_id=data.get("id", str(uuid4())),
            content=choice["message"]["content"],
            finish_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
            latency_ms=latency_ms,
            cost_usd=self._calculate_cost(data.get("usage", {})),
            model_name=self.config.model_name,
            provider=ModelProvider.OPENAI,
        )

    async def stream_generate(self, request: ModelRequest):
        api_key = self.config.metadata.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        messages = self._format_messages(request)
        payload = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stream": True,
        }

        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if data.get("choices"):
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield StreamingChunk(
                                    content=delta["content"],
                                    finish_reason=data["choices"][0].get("finish_reason"),
                                )
                    except json.JSONDecodeError:
                        continue

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        api_key = self.config.metadata.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model or "text-embedding-3-large",
            "input": texts,
        }

        response = await self._make_request(
            "POST",
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self.config.metadata.get('api_key', '')}",
                "Content-Type": "application/json",
            },
            json_data=payload,
        )

        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def health_check(self) -> bool:
        try:
            api_key = self.config.metadata.get("api_key", "") or os.environ.get(
                "OPENAI_API_KEY", ""
            )
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await self._make_request("GET", f"{self.base_url}/models", headers)
            return response.is_success
        except Exception:
            return False

    def _format_messages(self, request: ModelRequest) -> list[dict[str, str]]:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        messages.extend(request.messages)
        return messages

    def _calculate_cost(self, usage: dict[str, int]) -> float:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return (
            prompt_tokens * self.config.cost_per_1k_input
            + completion_tokens * self.config.cost_per_1k_output
        ) / 1000


class AnthropicProvider(ModelProviderBase):
    """Anthropic provider (fallback)."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.anthropic.com/v1"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        api_key = self.config.metadata.get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        messages = []
        if request.system_prompt:
            messages.append({"role": "user", "content": request.system_prompt})
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        messages.extend(request.messages)

        payload = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stop_sequences": request.stop,
        }

        start = time.time()
        response = await self._make_request(
            "POST",
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.config.metadata.get("api_key", ""),
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json_data=payload,
        )
        latency_ms = int((time.time() - start) * 1000)

        data = response.json()

        return ModelResponse(
            model_id=data.get("id", str(uuid4())),
            content=data["content"][0]["text"],
            finish_reason=data.get("stop_reason", "stop"),
            usage=data.get("usage", {}),
            latency_ms=latency_ms,
            cost_usd=self._calculate_cost(data.get("usage", {})),
            model_name=self.config.model_name,
            provider=ModelProvider.ANTHROPIC,
        )

    async def stream_generate(self, request: ModelRequest):
        """Generate a streaming response using Anthropic's Messages API."""
        api_key = self.config.metadata.get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "Accept": "text/event-stream",
        }

        messages = []
        if request.system_prompt:
            messages.append({"role": "user", "content": request.system_prompt})
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        messages.extend(request.messages)

        payload: dict[str, Any] = {
            "model": request.model or self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "top_p": request.top_p,
            "stream": True,
        }
        if request.stop:
            payload["stop_sequences"] = request.stop

        client = self._get_client()
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type", "")
                            if event_type == "content_block_delta":
                                delta = data.get("delta", {})
                                text = delta.get("text", "")
                                if text:
                                    yield StreamingChunk(content=text)
                            elif event_type == "message_stop":
                                yield StreamingChunk(content="", finish_reason="stop")
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPStatusError as e:
            logger.error("Anthropic streaming failed: %s", e)
            yield StreamingChunk(content="", finish_reason="error")

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        # Anthropic doesn't have embeddings API
        return []

    async def health_check(self) -> bool:
        try:
            api_key = self.config.metadata.get("api_key", "") or os.environ.get(
                "ANTHROPIC_API_KEY", ""
            )
            headers = {"x-api-key": api_key}
            response = await self._make_request("GET", f"{self.base_url}/models", headers)
            return response.is_success
        except Exception:
            return False

    def _calculate_cost(self, usage: dict[str, int]) -> float:
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        return (
            prompt_tokens * self.config.cost_per_1k_input
            + completion_tokens * self.config.cost_per_1k_output
        ) / 1000


class ModelRouter:
    """Routes requests to the best available model provider."""

    def __init__(
        self,
        providers: list[ModelProviderBase] | None = None,
        default_priority_order: list[ModelProvider] | None = None,
    ):
        self.providers: dict[ModelProvider, ModelProviderBase] = {}
        self._provider_order = default_priority_order or [
            ModelProvider.NVIDIA_NIM,
            ModelProvider.OPENAI,
            ModelProvider.ANTHROPIC,
        ]

        if providers:
            for p in providers:
                self.register_provider(p)

    def register_provider(self, provider: ModelProviderBase) -> None:
        """Register a model provider."""
        self.providers[provider.config.provider] = provider
        if provider.config.provider not in self._provider_order:
            self._provider_order.append(provider.config.provider)
        logger.info(
            "Registered model provider: %s (%s)",
            provider.config.provider.value,
            provider.config.model_name,
        )

    def unregister_provider(self, provider: ModelProvider) -> bool:
        """Unregister a provider."""
        if provider in self.providers:
            del self.providers[provider]
            self._provider_order.remove(provider)
            return True
        return False

    def get_provider(self, provider: ModelProvider) -> ModelProviderBase | None:
        """Get a specific provider."""
        return self.providers.get(provider)

    def get_available_providers(self) -> list[ModelProvider]:
        """Get list of available (enabled) providers in priority order."""
        return [
            p
            for p in self._provider_order
            if p in self.providers and self.providers[p].config.enabled
        ]

    async def generate(
        self,
        request: ModelRequest,
        preferred_provider: ModelProvider | None = None,
        required_capabilities: list[ModelCapability] | None = None,
    ) -> ModelResponse:
        """Generate a response, trying providers in priority order."""
        providers_to_try = []

        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(self.providers[preferred_provider])
        else:
            for p in self.get_available_providers():
                provider = self.providers[p]
                if required_capabilities:
                    if all(cap in provider.config.capabilities for cap in required_capabilities):
                        providers_to_try.append(provider)
                else:
                    providers_to_try.append(provider)

        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(
                    "Attempting generation with %s (%s)",
                    provider.config.provider.value,
                    provider.config.model_name,
                )
                response = await provider.generate(request)
                logger.info(
                    "Successfully generated with %s (latency: %dms)",
                    provider.config.provider.value,
                    response.latency_ms,
                )
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider %s failed: %s, trying next", provider.config.provider.value, e
                )
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def stream_generate(
        self,
        request: ModelRequest,
        preferred_provider: ModelProvider | None = None,
    ):
        """Stream generate from the best available provider."""
        preferred = preferred_provider or self.get_available_providers()[0]
        if preferred in self.providers:
            async for chunk in self.providers[preferred].stream_generate(request):
                yield chunk
        else:
            yield StreamingChunk(content="", finish_reason="no_provider")

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        preferred_provider: ModelProvider | None = None,
    ) -> list[list[float]]:
        """Generate embeddings."""
        provider = preferred_provider or ModelProvider.NVIDIA_NIM
        if provider in self.providers:
            return await self.providers[provider].embed(texts, model)
        # Try any provider with embedding capability
        for p in self.get_available_providers():
            if ModelCapability.EMBEDDING in self.providers[p].config.capabilities:
                return await self.providers[p].embed(texts, model)
        raise RuntimeError("No provider with embedding capability available")

    async def health_check_all(self) -> dict[ModelProvider, bool]:
        """Check health of all providers."""
        results = {}
        for p, provider in self.providers.items():
            try:
                results[p] = await provider.health_check()
            except Exception:
                results[p] = False
        return results

    def get_all_stats(self) -> dict[ModelProvider, dict[str, Any]]:
        """Get statistics for all providers."""
        return {p: provider.get_stats() for p, provider in self.providers.items()}

    async def close(self) -> None:
        """Close all providers."""
        for provider in self.providers.values():
            await provider.close()


# Default model configurations
DEFAULT_MODELS = {
    ModelProvider.NVIDIA_NIM: [
        ModelConfig(
            provider=ModelProvider.NVIDIA_NIM,
            model_name="meta/llama-3.1-70b-instruct",
            display_name="Llama 3.1 70B Instruct (NIM)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.CODE,
                ModelCapability.REASONING,
            ],
            max_tokens=8192,
            context_window=128000,
            cost_per_1k_input=0.0,  # NIM is self-hosted
            cost_per_1k_output=0.0,
            timeout_seconds=120,
            priority=0,
            metadata={"api_key": ""},
        ),
        ModelConfig(
            provider=ModelProvider.NVIDIA_NIM,
            model_name="nvidia/nemotron-3-ultra",
            display_name="Nemotron 3 Ultra (NIM)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.CODE,
                ModelCapability.REASONING,
            ],
            max_tokens=8192,
            context_window=128000,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            timeout_seconds=120,
            priority=1,
            metadata={"api_key": ""},
        ),
    ],
    ModelProvider.OPENAI: [
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            display_name="GPT-4o",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.CODE,
            ],
            max_tokens=4096,
            context_window=128000,
            cost_per_1k_input=5.0,
            cost_per_1k_output=15.0,
            timeout_seconds=60,
            priority=10,
            metadata={"api_key": ""},
        ),
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
            ],
            max_tokens=4096,
            context_window=128000,
            cost_per_1k_input=0.15,
            cost_per_1k_output=0.6,
            timeout_seconds=60,
            priority=11,
            metadata={"api_key": ""},
        ),
    ],
    ModelProvider.ANTHROPIC: [
        ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            display_name="Claude 3.5 Sonnet",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.CODE,
            ],
            max_tokens=8192,
            context_window=200000,
            cost_per_1k_input=3.0,
            cost_per_1k_output=15.0,
            timeout_seconds=60,
            priority=20,
            metadata={"api_key": ""},
        ),
    ],
}


class ModelRouterFacade:
    """Main model router facade."""

    def __init__(
        self,
        router: ModelRouter | None = None,
    ):
        self.router = router or self._create_default_router()

    def _create_default_router(self) -> ModelRouter:
        router = ModelRouter()
        for provider_type, configs in DEFAULT_MODELS.items():
            for config in configs:
                if provider_type == ModelProvider.NVIDIA_NIM:
                    router.register_provider(NVIDIANIMProvider(config))
                elif provider_type == ModelProvider.OPENAI:
                    router.register_provider(OpenAIProvider(config))
                elif provider_type == ModelProvider.ANTHROPIC:
                    router.register_provider(AnthropicProvider(config))
        return router

    async def generate(
        self,
        request: ModelRequest,
        preferred_provider: ModelProvider | None = None,
        required_capabilities: list[ModelCapability] | None = None,
    ) -> ModelResponse:
        return await self.router.generate(request, preferred_provider, required_capabilities)

    async def stream_generate(
        self,
        request: ModelRequest,
        preferred_provider: ModelProvider | None = None,
    ):
        async for chunk in self.router.stream_generate(request, preferred_provider):
            yield chunk

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        preferred_provider: ModelProvider | None = None,
    ) -> list[list[float]]:
        return await self.router.embed(texts, model, preferred_provider)

    async def health_check_all(self) -> dict[ModelProvider, bool]:
        return await self.router.health_check_all()

    def get_all_stats(self) -> dict:
        return self.router.get_all_stats()

    def get_available_providers(self) -> list[ModelProvider]:
        return self.router.get_available_providers()

    async def close(self) -> None:
        await self.router.close()


# Global instances
_model_router: ModelRouter | None = None
_model_router_facade: ModelRouterFacade | None = None


def get_model_router() -> ModelRouter:
    """Get the global model router."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router


def get_model_router_facade() -> ModelRouterFacade:
    """Get the ModelRouter facade (higher-level interface)."""
    global _model_router_facade
    if _model_router_facade is None:
        _model_router_facade = ModelRouterFacade()
    return _model_router_facade
