from unittest.mock import AsyncMock, MagicMock, patch

from jose import JWTError

from app.infrastructure.auth.supabase_jwt import SupabaseJWTVerifier


class TestInit:
    def test_jwks_url_constructed(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = ""

            verifier = SupabaseJWTVerifier()

            assert verifier._jwks_url == "https://project.supabase.co/auth/v1/.well-known/jwks.json"

    def test_no_url_no_jwks_url(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = ""

            verifier = SupabaseJWTVerifier()

            assert verifier._jwks_url == ""


class TestEnabled:
    def test_enabled_with_config(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "anon_key_123"

            verifier = SupabaseJWTVerifier()

            assert verifier.enabled is True

    def test_disabled_no_url(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = ""
            mock_cfg.supabase_anon_key = "anon_key_123"

            verifier = SupabaseJWTVerifier()

            assert verifier.enabled is False

    def test_disabled_no_key(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = ""

            verifier = SupabaseJWTVerifier()

            assert verifier.enabled is False


class TestFetchJwks:
    async def test_cached_returned(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._jwks = {"keys": []}

            result = await verifier._fetch_jwks()

            assert result == {"keys": []}

    async def test_disabled_returns_none(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = ""
            mock_cfg.supabase_anon_key = ""

            verifier = SupabaseJWTVerifier()

            result = await verifier._fetch_jwks()

            assert result is None

    async def test_successful_fetch(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"keys": [{"kid": "abc"}]}
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_resp)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await verifier._fetch_jwks()

                assert result == {"keys": [{"kid": "abc"}]}
                assert verifier._jwks == {"keys": [{"kid": "abc"}]}

    async def test_fetch_error(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=Exception("Connection error"))

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await verifier._fetch_jwks()

                assert result is None


class TestVerifyToken:
    async def test_no_jwks_returns_none(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._fetch_jwks = AsyncMock(return_value=None)

            result = await verifier.verify_token("some_token")

            assert result is None

    async def test_no_kid_in_header(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._fetch_jwks = AsyncMock(return_value={"keys": []})

            with patch("jose.jwt.get_unverified_header", return_value={}):
                result = await verifier.verify_token("some_token")

                assert result is None

    async def test_kid_not_in_jwks(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._fetch_jwks = AsyncMock(return_value={"keys": [{"kid": "other"}]})

            with patch("jose.jwt.get_unverified_header", return_value={"kid": "missing"}):
                result = await verifier.verify_token("some_token")

                assert result is None

    async def test_successful_verification(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._fetch_jwks = AsyncMock(
                return_value={"keys": [{"kid": "abc", "n": "n", "e": "e"}]}
            )

            with patch("jose.jwt.get_unverified_header", return_value={"kid": "abc"}):
                with patch("app.infrastructure.auth.supabase_jwt.RSAKey"):
                    with patch("jose.jwt.decode", return_value={"sub": "user_123"}):
                        result = await verifier.verify_token("valid_token")

                        assert result == {"sub": "user_123"}

    async def test_jwt_decode_error(self):
        with patch("app.infrastructure.auth.supabase_jwt.config") as mock_cfg:
            mock_cfg.supabase_url = "https://project.supabase.co"
            mock_cfg.supabase_anon_key = "key"

            verifier = SupabaseJWTVerifier()
            verifier._fetch_jwks = AsyncMock(
                return_value={"keys": [{"kid": "abc", "n": "n", "e": "e"}]}
            )

            with patch("jose.jwt.get_unverified_header", return_value={"kid": "abc"}):
                with patch("app.infrastructure.auth.supabase_jwt.RSAKey"):
                    with patch("jose.jwt.decode", side_effect=JWTError("Invalid signature")):
                        result = await verifier.verify_token("invalid_token")

                        assert result is None
