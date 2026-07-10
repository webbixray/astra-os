from pydantic_settings import BaseSettings
from redis.asyncio import Redis


class RedisConfig(BaseSettings):
    url: str = "redis://localhost:6379/0"

    model_config = {"env_prefix": "redis_"}


class RedisCache:
    def __init__(self, config: RedisConfig | None = None):
        self.config = config or RedisConfig()
        self.client: Redis | None = None

    async def connect(self) -> None:
        self.client = await Redis.from_url(
            self.config.url,
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        if self.client is not None:
            await self.client.close()

    async def get(self, key: str) -> str | None:
        if self.client is None:
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        if self.client is None:
            return
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        if self.client is None:
            return
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        if self.client is None:
            return False
        return await self.client.exists(key) > 0
