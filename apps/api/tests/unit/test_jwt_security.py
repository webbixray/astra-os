from __future__ import annotations

from app.infrastructure.auth.jwt import JWTConfig, JWTService, RefreshTokenStore


class TestJWTService:
    def setup_method(self):
        self.config = JWTConfig(
            secret_key="test-secret-key-that-is-at-least-32-chars!!",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )
        self.service = JWTService(self.config)

    def test_create_and_verify_access_token(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_access_token(user_id)
        payload = self.service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert payload["iss"] == "astra-os"
        assert payload["aud"] == "astra-api"

    def test_create_and_verify_refresh_token(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_refresh_token(user_id)
        payload = self.service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_invalid_token(self):
        payload = self.service.verify_token("invalid-token")
        assert payload is None

    def test_expired_token(self):
        expired_config = JWTConfig(
            secret_key="test-secret-key-that-is-at-least-32-chars!!",
            access_token_expire_minutes=-1,
        )
        service = JWTService(expired_config)
        token = service.create_access_token("user-id")
        payload = service.verify_token(token)
        assert payload is None

    def test_wrong_secret(self):
        service1 = JWTService(self.config)
        service2 = JWTService(
            JWTConfig(secret_key="different-secret-key-that-is-at-least-32-chars!")
        )
        token = service1.create_access_token("user-id")
        payload = service2.verify_token(token)
        assert payload is None

    def test_token_contains_jti(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_access_token(user_id)
        payload = self.service.verify_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) == 16

    def test_token_contains_version(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_access_token(user_id)
        payload = self.service.verify_token(token)
        assert payload["ver"] == 1

    def test_extra_claims(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_access_token(user_id, extra_claims={"org_id": "org-123"})
        payload = self.service.verify_token(token)
        assert payload["org_id"] == "org-123"


class TestRefreshTokenRotation:
    def setup_method(self):
        RefreshTokenStore._memory_revoked.clear()
        RefreshTokenStore._memory_fingerprints.clear()
        self.config = JWTConfig(
            secret_key="test-secret-key-that-is-at-least-32-chars!!",
        )
        self.service = JWTService(self.config)

    def test_rotate_refresh_token(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        old_token = self.service.create_refresh_token(user_id)
        result = self.service.rotate_refresh_token(old_token)
        assert result is not None
        new_access, new_refresh = result
        assert self.service.verify_token(new_access) is not None
        assert self.service.verify_token(new_refresh) is not None
        assert self.service.verify_token(old_token) is None

    def test_rotate_invalid_token(self):
        result = self.service.rotate_refresh_token("invalid-token")
        assert result is None

    def test_rotate_access_token_fails(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        access_token = self.service.create_access_token(user_id)
        result = self.service.rotate_refresh_token(access_token)
        assert result is None

    def test_revoked_token_rejected(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = self.service.create_refresh_token(user_id)
        RefreshTokenStore._memory_revoked.add(RefreshTokenStore.fingerprint(token))
        payload = self.service.verify_token(token)
        assert payload is None
