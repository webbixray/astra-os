from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    url: str = "postgresql+asyncpg://astra:astra_dev@localhost:5432/astra"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600

    model_config = {"env_prefix": "database_"}
