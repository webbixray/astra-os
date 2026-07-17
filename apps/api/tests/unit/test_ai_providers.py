from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.external_adapters.ai.router import (
    AIRouter,
    NvidiaNIMProvider,
    OpenAIProvider,
)


@pytest.fixture(autouse=True)
def clear_config():
    import app.config as cfg
    original_nvidia = cfg.config.nvidia_nim_base_url
    original_openai = cfg.config.openai_api_key
    yield
    cfg.config.nvidia_nim_base_url = original_nvidia
    cfg.config.openai_api_key = original_openai


class TestNvidiaNIMProvider:
    @pytest.mark.asyncio
    async def test_chat_no_base_url_returns_empty(self):
        provider = NvidiaNIMProvider()
        result = await provider.chat([{"role": "user", "content": "Hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_stream_chat_no_base_url_returns_nothing(self):
        provider = NvidiaNIMProvider()
        chunks = []
        async for chunk in provider.stream_chat([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == []

    @pytest.mark.asyncio
    async def test_chat_returns_content(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "Hello from NVIDIA"}}]
        })

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with patch("app.infrastructure.external_adapters.ai.router.config") as mock_config:
            mock_config.nvidia_nim_base_url = "https://nvidia.example.com"
            mock_config.nvidia_nim_api_key = "test-key"

            with patch("httpx.AsyncClient", return_value=mock_client):
                provider = NvidiaNIMProvider()
                result = await provider.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello from NVIDIA"

    @pytest.mark.asyncio
    async def test_stream_chat_yields_content(self):
        provider = NvidiaNIMProvider()

        with patch("app.infrastructure.external_adapters.ai.router.config") as mock_config:
            mock_config.nvidia_nim_base_url = "https://nvidia.example.com"
            mock_config.nvidia_nim_api_key = "test-key"

            lines = [
                'data: {"choices": [{"delta": {"content": "Hello"}}]}',
                'data: {"choices": [{"delta": {"content": " world"}}]}',
                "data: [DONE]",
            ]

            mock_response = MagicMock()
            mock_response.aiter_lines.return_value.__aiter__.return_value = iter(lines)

            mock_stream_ctx = MagicMock()
            mock_stream_ctx.__aenter__.return_value = mock_response

            mock_client = MagicMock()
            mock_client.stream.return_value = mock_stream_ctx
            mock_client_ctx = MagicMock()
            mock_client_ctx.__aenter__.return_value = mock_client

            with patch("httpx.AsyncClient", return_value=mock_client_ctx):
                chunks = []
                async for chunk in provider.stream_chat([{"role": "user", "content": "Hi"}]):
                    chunks.append(chunk)

        assert chunks == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_stream_chat_skips_json_errors(self):
        provider = NvidiaNIMProvider()

        with patch("app.infrastructure.external_adapters.ai.router.config") as mock_config:
            mock_config.nvidia_nim_base_url = "https://nvidia.example.com"
            mock_config.nvidia_nim_api_key = "test-key"

            lines = [
                "data: invalid json",
                'data: {"choices": [{"delta": {"content": "OK"}}]}',
                "data: [DONE]",
            ]

            mock_response = MagicMock()
            mock_response.aiter_lines.return_value.__aiter__.return_value = iter(lines)

            mock_stream_ctx = MagicMock()
            mock_stream_ctx.__aenter__.return_value = mock_response

            mock_client = MagicMock()
            mock_client.stream.return_value = mock_stream_ctx
            mock_client_ctx = MagicMock()
            mock_client_ctx.__aenter__.return_value = mock_client

            with patch("httpx.AsyncClient", return_value=mock_client_ctx):
                chunks = []
                async for chunk in provider.stream_chat([{"role": "user", "content": "Hi"}]):
                    chunks.append(chunk)

        assert chunks == ["OK"]


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_chat_no_api_key_returns_empty(self):
        import app.config as cfg
        cfg.config.openai_api_key = ""

        provider = OpenAIProvider()
        result = await provider.chat([{"role": "user", "content": "Hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_stream_chat_no_api_key_returns_nothing(self):
        import app.config as cfg
        cfg.config.openai_api_key = ""

        provider = OpenAIProvider()
        chunks = []
        async for chunk in provider.stream_chat([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == []

    @pytest.mark.asyncio
    async def test_chat_returns_content(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "Hello from OpenAI"}}]
        })

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with patch("app.infrastructure.external_adapters.ai.router.config") as mock_config:
            mock_config.openai_api_key = "sk-test"

            with patch("httpx.AsyncClient", return_value=mock_client):
                provider = OpenAIProvider()
                result = await provider.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello from OpenAI"

    @pytest.mark.asyncio
    async def test_stream_chat_yields_content(self):
        provider = OpenAIProvider()
        provider.api_key = "sk-xxx"

        lines = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.aiter_lines.return_value.__aiter__.return_value = iter(lines)

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__.return_value = mock_response

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream_ctx
        mock_client_ctx = MagicMock()
        mock_client_ctx.__aenter__.return_value = mock_client

        with patch("app.infrastructure.external_adapters.ai.router.config") as mock_config:
            mock_config.openai_api_key = "sk-test"

            with patch("httpx.AsyncClient", return_value=mock_client_ctx):
                chunks = []
                async for chunk in provider.stream_chat([{"role": "user", "content": "Hi"}]):
                    chunks.append(chunk)

        assert chunks == ["Hello", " world"]


class TestAIRouter:
    def test_init_no_providers_when_disabled(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = ""
        cfg.config.openai_api_key = ""
        router = AIRouter()
        assert router.providers == []

    def test_init_with_nvidia_only(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = ""
        router = AIRouter()
        assert len(router.providers) == 1
        assert isinstance(router.providers[0], NvidiaNIMProvider)

    def test_init_with_openai_only(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = ""
        cfg.config.openai_api_key = "sk-xxx"
        router = AIRouter()
        assert len(router.providers) == 1
        assert isinstance(router.providers[0], OpenAIProvider)

    def test_init_with_both_providers(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = "sk-xxx"
        router = AIRouter()
        assert len(router.providers) == 2

    @pytest.mark.asyncio
    async def test_chat_no_providers_returns_fallback(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = ""
        cfg.config.openai_api_key = ""
        router = AIRouter()
        result = await router.chat([{"role": "user", "content": "Hi"}])
        assert result == "I'm sorry, I'm having trouble connecting to my AI services right now."

    @pytest.mark.asyncio
    async def test_chat_uses_first_provider(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = ""

        router = AIRouter()
        provider = router.providers[0]
        provider.chat = AsyncMock(return_value="NVIDIA response")
        result = await router.chat([{"role": "user", "content": "Hi"}])
        assert result == "NVIDIA response"

    @pytest.mark.asyncio
    async def test_chat_falls_back_to_next_provider(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = "sk-xxx"

        router = AIRouter()
        router.providers[0].chat = AsyncMock(side_effect=RuntimeError("NVIDIA down"))
        router.providers[1].chat = AsyncMock(return_value="OpenAI response")
        result = await router.chat([{"role": "user", "content": "Hi"}])
        assert result == "OpenAI response"

    @pytest.mark.asyncio
    async def test_chat_all_fail_returns_fallback(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = "sk-xxx"

        router = AIRouter()
        router.providers[0].chat = AsyncMock(side_effect=RuntimeError("NVIDIA down"))
        router.providers[1].chat = AsyncMock(side_effect=RuntimeError("OpenAI down"))
        result = await router.chat([{"role": "user", "content": "Hi"}])
        assert result == "I'm sorry, I'm having trouble connecting to my AI services right now."

    @pytest.mark.asyncio
    async def test_stream_chat_falls_back_to_next_provider(self):
        import app.config as cfg
        cfg.config.nvidia_nim_base_url = "https://nvidia.example.com"
        cfg.config.openai_api_key = "sk-xxx"

        # Create proper async generator functions that return async iterators
        async def nvidia_stream(messages, model=None):
            raise RuntimeError("NVIDIA down")
            yield  # pragma: no cover

        async def openai_stream(messages, model=None):
            yield "OpenAI chunk"

        router = AIRouter()
        # Replace the stream_chat method on the providers directly
        # The stream_chat methods should return async iterators when called
        router.providers[0].stream_chat = nvidia_stream
        router.providers[1].stream_chat = openai_stream

        chunks = []
        async for chunk in router.stream_chat([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["OpenAI chunk"]
