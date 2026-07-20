"""Shared test fixtures and helpers for ASTRA OS API tests."""

from collections.abc import AsyncGenerator
from typing import Any

import hashlib
import hmac
import secrets
import time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import config
from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.domain.entities.user import User
from app.infrastructure.db.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def _replace_jsonb_with_json(model_class: type) -> None:
    for col in model_class.__table__.c:
        if isinstance(col.type, (JSONB, ARRAY)):
            col.type = JSON()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    for model_class in Base.registry.mappers:
        _replace_jsonb_with_json(model_class.class_)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def sample_user() -> User:
    return User.create(email="test@example.com", name="Test User")


@pytest.fixture
def sample_org() -> Organization:
    return Organization.create(name="Test Org", slug="test-org")


@pytest.fixture
def sample_team_member(sample_user: User, sample_org: Organization) -> TeamMember:
    return TeamMember.create(
        organization_id=sample_org.id,
        user_id=sample_user.id,
        role="owner",
    )


def setup_csrf(test_client: AsyncClient) -> dict[str, str]:
    """Configure CSRF tokens on the test client for POST/PUT/PATCH/DELETE requests.

    Call this before making mutating requests. Sets the Cookie header with
    csrf + session tokens and returns a dict of headers to pass to each request.

    Usage:
        csrf_headers = setup_csrf(test_client)
        response = await test_client.post("/api/endpoint", headers=csrf_headers, json={...})
    """
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    test_client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
    return {"X-CSRF-Token": csrf_token}
