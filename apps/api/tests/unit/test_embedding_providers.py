from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.external_adapters.knowledge.embedding_service import (
    NvidiaEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)

FALLBACK_DIM = 32  # SHA-256 produces 32 bytes


class TestFallbackEmbed:
    def test_fallback_is_deterministic(self):
        provider = NvidiaEmbeddingProvider()
        vec1 = provider._fallback_embed("hello world")
        vec2 = provider._fallback_embed("hello world")
        assert vec1 == vec2

    def test_fallback_different_inputs_differ(self):
        provider = NvidiaEmbeddingProvider()
        vec1 = provider._fallback_embed("hello")
        vec2 = provider._fallback_embed("world")
        assert vec1 != vec2

    def test_fallback_has_correct_length(self):
        provider = NvidiaEmbeddingProvider()
        vec = provider._fallback_embed("test")
        assert len(vec) == FALLBACK_DIM

    def test_fallback_is_normalized(self):
        provider = NvidiaEmbeddingProvider()
        vec = provider._fallback_embed("test")
        norm = sum(v * v for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_fallback_empty_string(self):
        provider = NvidiaEmbeddingProvider()
        vec = provider._fallback_embed("")
        assert len(vec) == FALLBACK_DIM
        norm = sum(v * v for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6


class TestNvidiaEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_no_base_url_uses_fallback(self):
        provider = NvidiaEmbeddingProvider()
        provider.base_url = ""
        vec = await provider.embed("hello")
        assert len(vec) == FALLBACK_DIM

    @pytest.mark.asyncio
    async def test_embed_success_returns_embedding(self):
        provider = NvidiaEmbeddingProvider()
        provider.base_url = "https://nvidia.example.com"
        provider.api_key = "tok"

        expected = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"data": [{"embedding": expected}]})

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.embed("test text")

        assert result == expected

    @pytest.mark.asyncio
    async def test_embed_error_uses_fallback(self):
        provider = NvidiaEmbeddingProvider()
        provider.base_url = "https://nvidia.example.com"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=RuntimeError("API error"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.embed("test text")

        assert len(result) == FALLBACK_DIM

    @pytest.mark.asyncio
    async def test_embed_batch_calls_embed_for_each(self):
        provider = NvidiaEmbeddingProvider()
        provider.base_url = ""

        results = await provider.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        for vec in results:
            assert len(vec) == FALLBACK_DIM
        assert results[0] != results[1]


class TestOpenAIEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_no_api_key_uses_fallback(self):
        provider = OpenAIEmbeddingProvider()
        provider.api_key = ""
        vec = await provider.embed("hello")
        assert len(vec) == FALLBACK_DIM

    @pytest.mark.asyncio
    async def test_embed_success_returns_embedding(self):
        provider = OpenAIEmbeddingProvider()
        provider.api_key = "sk-xxx"

        expected = [0.4, 0.5, 0.6]
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"data": [{"embedding": expected}]})

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.embed("test text")

        assert result == expected

    @pytest.mark.asyncio
    async def test_embed_error_uses_fallback(self):
        provider = OpenAIEmbeddingProvider()
        provider.api_key = "sk-xxx"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=RuntimeError("API error"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.embed("test text")

        assert len(result) == FALLBACK_DIM

    @pytest.mark.asyncio
    async def test_embed_batch_returns_correct_count(self):
        provider = OpenAIEmbeddingProvider()
        provider.api_key = ""

        results = await provider.embed_batch(["x", "y"])
        assert len(results) == 2


class TestGetEmbeddingProvider:
    def test_nvidia_first_if_configured(self):
        import app.config as cfg

        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = ""
        provider = get_embedding_provider()
        assert isinstance(provider, NvidiaEmbeddingProvider)

    def test_openai_if_no_nvidia(self):
        import app.config as cfg

        cfg.config.nvidia_nim_base_url = ""
        cfg.config.openai_api_key = "sk-xxx"
        provider = get_embedding_provider()
        assert isinstance(provider, OpenAIEmbeddingProvider)

    def test_defaults_to_nvidia(self):
        import app.config as cfg

        cfg.config.nvidia_nim_base_url = ""
        cfg.config.openai_api_key = ""
        provider = get_embedding_provider()
        assert isinstance(provider, NvidiaEmbeddingProvider)
