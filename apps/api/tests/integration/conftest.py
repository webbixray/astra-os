from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.auth.jwt import RefreshTokenStore
from app.infrastructure.db.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


def _replace_jsonb_with_json(model_class: type) -> None:
    for col in model_class.__table__.c:
        if isinstance(col.type, (JSONB, ARRAY)):
            col.type = JSON()


@pytest.fixture(autouse=True)
def _clear_refresh_token_store():
    RefreshTokenStore._memory_revoked.clear()
    RefreshTokenStore._memory_fingerprints.clear()


@pytest_asyncio.fixture
async def integration_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    for mapper in Base.registry.mappers:
        _replace_jsonb_with_json(mapper.class_)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def integration_session_factory(integration_engine):
    return async_sessionmaker(
        integration_engine, class_=AsyncSession, expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def integration_db(integration_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with integration_session_factory() as session:
        yield session
