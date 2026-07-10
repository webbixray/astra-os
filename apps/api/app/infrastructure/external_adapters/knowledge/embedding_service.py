import logging

import httpx

from app.application.ports.embedding_provider import EmbeddingProvider
from app.config import config

logger = logging.getLogger(__name__)


class NvidiaEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.base_url = config.nvidia_nim_base_url
        self.api_key = ""

    async def embed(self, text: str) -> list[float]:
        if not self.base_url:
            return self._fallback_embed(text)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": text, "model": "nvidia/nv-embed-qa-4-v2"},
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning("NVIDIA embedding failed, using fallback: %s", e)
            return self._fallback_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results

    def _fallback_embed(self, text: str) -> list[float]:
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vec = [b / 255.0 for b in hash_bytes[:384]]
        norm = sum(v * v for v in vec) ** 0.5
        return [v / norm for v in vec]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.api_key = config.openai_api_key

    async def embed(self, text: str) -> list[float]:
        if not self.api_key:
            return NvidiaEmbeddingProvider()._fallback_embed(text)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": text, "model": "text-embedding-3-small"},
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning("OpenAI embedding failed, using fallback: %s", e)
            return NvidiaEmbeddingProvider()._fallback_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results


def get_embedding_provider() -> EmbeddingProvider:
    if config.nvidia_nim_base_url:
        return NvidiaEmbeddingProvider()
    if config.openai_api_key:
        return OpenAIEmbeddingProvider()
    return NvidiaEmbeddingProvider()
