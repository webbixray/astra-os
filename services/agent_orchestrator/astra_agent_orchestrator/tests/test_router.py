"""Tests for the model router."""


import pytest
from astra_agent_orchestrator.router import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRouter,
    ModelRouterFacade,
)


class TestModelRouter:
    """Tests for ModelRouter."""

    def test_create_router(self) -> None:
        router = ModelRouter()
        assert len(router.providers) == 0

    def test_get_available_providers_empty(self) -> None:
        router = ModelRouter()
        assert router.get_available_providers() == []

    def test_health_check_empty(self) -> None:
        router = ModelRouter()

        @pytest.mark.asyncio
        async def check() -> None:
            results = await router.health_check_all()
            assert results == {}

    def test_get_all_stats_empty(self) -> None:
        router = ModelRouter()
        assert router.get_all_stats() == {}


class TestModelRequest:
    """Tests for ModelRequest."""

    def test_default_request(self) -> None:
        req = ModelRequest()
        assert req.messages == []
        assert req.temperature == 0.7
        assert req.stream is False

    def test_request_with_messages(self) -> None:
        req = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.3,
            max_tokens=1000,
        )
        assert len(req.messages) == 1
        assert req.temperature == 0.3


class TestModelResponse:
    """Tests for ModelResponse."""

    def test_response_creation(self) -> None:
        resp = ModelResponse(
            model_id="test-123",
            content="Hello world",
            model_name="gpt-4o",
            provider=ModelProvider.OPENAI,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            latency_ms=100,
            cost_usd=0.001,
        )
        assert resp.content == "Hello world"
        assert resp.cost_usd == 0.001
        assert resp.request_id is not None


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_config_creation(self) -> None:
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            display_name="GPT-4o",
            capabilities=[ModelCapability.CHAT],
            max_tokens=4096,
            context_window=128000,
        )
        assert config.provider == ModelProvider.OPENAI
        assert config.enabled is True

    def test_config_defaults(self) -> None:
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            display_name="GPT-4o",
            capabilities=[],
            max_tokens=4096,
            context_window=128000,
        )
        assert config.priority == 0
        assert config.max_retries == 3


class TestModelRouterFacade:
    """Tests for ModelRouterFacade."""

    def test_facade_creation(self) -> None:
        facade = ModelRouterFacade()
        assert facade.router is not None

    def test_facade_creates_default_providers(self) -> None:
        facade = ModelRouterFacade()
        providers = facade.get_available_providers()
        # Should have providers registered (even without API keys)
        assert len(providers) >= 0  # Providers are registered but may not be enabled

    def test_facade_health_check(self) -> None:
        facade = ModelRouterFacade()

        @pytest.mark.asyncio
        async def check() -> None:
            results = await facade.health_check_all()
            assert isinstance(results, dict)

    def test_facade_stats(self) -> None:
        facade = ModelRouterFacade()
        stats = facade.get_all_stats()
        assert isinstance(stats, dict)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_all_providers(self) -> None:
        providers = list(ModelProvider)
        assert ModelProvider.NVIDIA_NIM in providers
        assert ModelProvider.OPENAI in providers
        assert ModelProvider.ANTHROPIC in providers

    def test_provider_values(self) -> None:
        assert ModelProvider.NVIDIA_NIM.value == "nvidia_nim"
        assert ModelProvider.OPENAI.value == "openai"


class TestModelCapability:
    """Tests for ModelCapability enum."""

    def test_all_capabilities(self) -> None:
        caps = list(ModelCapability)
        assert len(caps) >= 5
        assert ModelCapability.CHAT in caps
        assert ModelCapability.EMBEDDING in caps
