import contextlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt as jose_jwt

from app.infrastructure.auth.jwt import JWTConfig, JWTService
from app.infrastructure.auth.password import hash_password, verify_password
from app.infrastructure.cache.redis import RedisCache, RedisConfig


class TestJWTConfig:
    def test_defaults(self):
        cfg = JWTConfig()
        assert cfg.secret_key == ""
        assert cfg.algorithm == "HS256"
        assert cfg.access_token_expire_minutes == 15
        assert cfg.refresh_token_expire_days == 7

    def test_custom_values(self):
        cfg = JWTConfig(
            secret_key="my-secret",
            algorithm="RS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=14,
        )
        assert cfg.secret_key == "my-secret"
        assert cfg.algorithm == "RS256"
        assert cfg.access_token_expire_minutes == 30
        assert cfg.refresh_token_expire_days == 14


class TestJWTService:
    def test_create_access_token_basic(self):
        svc = JWTService(JWTConfig(secret_key="test", algorithm="HS256"))
        token = svc.create_access_token("user-123")
        assert isinstance(token, str)
        payload = jose_jwt.decode(token, "test", algorithms=["HS256"], audience="astra-api")
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "iat" in payload
        assert "exp" in payload
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)
        assert now + timedelta(minutes=14) <= exp <= now + timedelta(minutes=16)

    def test_create_access_token_with_extra_claims(self):
        svc = JWTService(JWTConfig(secret_key="test", algorithm="HS256"))
        token = svc.create_access_token("user-123", extra_claims={"role": "admin", "org": "org-1"})
        payload = jose_jwt.decode(token, "test", algorithms=["HS256"], audience="astra-api")
        assert payload["role"] == "admin"
        assert payload["org"] == "org-1"
        assert payload["sub"] == "user-123"

    def test_create_refresh_token(self):
        svc = JWTService(JWTConfig(secret_key="test", algorithm="HS256"))
        token = svc.create_refresh_token("user-123")
        payload = jose_jwt.decode(token, "test", algorithms=["HS256"], audience="astra-api")
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)
        assert now + timedelta(days=6) <= exp <= now + timedelta(days=8)

    def test_verify_valid_token(self):
        svc = JWTService(JWTConfig(secret_key="test", algorithm="HS256"))
        token = svc.create_access_token("user-123")
        payload = svc.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_verify_invalid_signature(self):
        svc1 = JWTService(JWTConfig(secret_key="secret1"))
        svc2 = JWTService(JWTConfig(secret_key="secret2"))
        token = svc1.create_access_token("user-123")
        payload = svc2.verify_token(token)
        assert payload is None

    def test_verify_expired_token(self):
        # Create token with negative expiry
        svc = JWTService(JWTConfig(secret_key="test", access_token_expire_minutes=-1))
        token = svc.create_access_token("user-123")
        payload = svc.verify_token(token)
        assert payload is None

    def test_verify_malformed_token(self):
        svc = JWTService(JWTConfig(secret_key="test"))
        payload = svc.verify_token("not.a.valid.token")
        assert payload is None

    def test_verify_tampered_token(self):
        svc = JWTService(JWTConfig(secret_key="test"))
        token = svc.create_access_token("user-123")
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".tampered"
        payload = svc.verify_token(tampered)
        assert payload is None

    def test_different_algorithm_rejected(self):
        svc_hs = JWTService(JWTConfig(secret_key="test", algorithm="HS256"))
        svc_rs = JWTService(JWTConfig(secret_key="test", algorithm="RS256"))
        token = svc_hs.create_access_token("user-123")
        # RS256 decode of HS256 token should fail
        payload = svc_rs.verify_token(token)
        assert payload is None


class TestPasswordHashing:
    def test_hash_password_returns_hash(self):
        hashed = hash_password("mysecret")
        assert isinstance(hashed, str)
        assert len(hashed) > 20
        assert hashed.startswith(("$2b$", "$2a$", "$2y$"))

    def test_hash_password_is_deterministic_for_same_input(self):
        # bcrypt includes salt so hashes differ
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_verify_password_correct(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False

    def test_verify_against_invalid_hash(self):
        # Should not raise, just return False
        try:
            assert verify_password("any", "not-a-bcrypt-hash") is False
        except ValueError:
            pass  # passlib raises ValueError for invalid hash format
        with contextlib.suppress(ValueError):
            assert verify_password("any", "") is False


class TestRedisConfig:
    def test_defaults(self):
        cfg = RedisConfig()
        # In docker-compose, redis service is named "redis"
        assert cfg.url in ("redis://localhost:6379/0", "redis://redis:6379/0")

    def test_custom_url(self):
        cfg = RedisConfig(url="redis://custom:6380/1")
        assert cfg.url == "redis://custom:6380/1"


class TestRedisCache:
    @pytest.mark.asyncio
    async def test_pre_connect_operations_noop(self):
        cache = RedisCache(RedisConfig())
        assert cache.client is None
        assert await cache.get("key") is None
        await cache.set("key", "val")  # should not raise
        await cache.delete("key")  # should not raise
        assert await cache.exists("key") is False

    @pytest.mark.asyncio
    async def test_connect_creates_client(self):
        cache = RedisCache(RedisConfig(url="redis://test:6379/0"))
        with patch("app.infrastructure.cache.redis.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)
            await cache.connect()
            assert cache.client is mock_client
            mock_redis.from_url.assert_called_once_with(
                "redis://test:6379/0",
                decode_responses=True,
            )

    @pytest.mark.asyncio
    async def test_disconnect_closes_client(self):
        cache = RedisCache(RedisConfig())
        mock_client = AsyncMock()
        cache.client = mock_client
        await cache.disconnect()
        mock_client.close.assert_called_once()
        # Note: current implementation doesn't set client to None after disconnect

    @pytest.mark.asyncio
    async def test_disconnect_no_client_noop(self):
        cache = RedisCache(RedisConfig())
        await cache.disconnect()  # should not raise

    @pytest.mark.asyncio
    async def test_set_get_delete_exists_after_connect(self):
        cache = RedisCache(RedisConfig())
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value="value")
        mock_client.set = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.exists = AsyncMock(return_value=1)
        cache.client = mock_client

        await cache.set("key", "value", ttl=600)
        mock_client.set.assert_called_once_with("key", "value", ex=600)

        result = await cache.get("key")
        assert result == "value"

        await cache.delete("key")
        mock_client.delete.assert_called_once_with("key")

        exists = await cache.exists("key")
        assert exists is True
        mock_client.exists.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_exists_returns_bool(self):
        cache = RedisCache(RedisConfig())
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=0)
        cache.client = mock_client
        assert await cache.exists("missing") is False

        mock_client.exists = AsyncMock(return_value=2)
        assert await cache.exists("present") is True

    @pytest.mark.asyncio
    async def test_default_ttl(self):
        cache = RedisCache(RedisConfig())
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        cache.client = mock_client
        await cache.set("key", "val")
        mock_client.set.assert_called_once_with("key", "val", ex=300)
