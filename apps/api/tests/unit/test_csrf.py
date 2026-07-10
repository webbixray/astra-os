from __future__ import annotations

import time

from app.presentation.middleware.csrf import _generate_csrf_token, _verify_csrf_token


class TestCSRFToken:
    def test_generate_and_verify(self):
        secret = "test-secret-key-1234567890abcdef"
        session_id = "abc123"
        token = _generate_csrf_token(secret, session_id)
        assert _verify_csrf_token(token, secret, session_id)

    def test_wrong_secret(self):
        secret = "test-secret-key-1234567890abcdef"
        session_id = "abc123"
        token = _generate_csrf_token(secret, session_id)
        assert not _verify_csrf_token(token, "wrong-secret-1234567890abcdef", session_id)

    def test_wrong_session(self):
        secret = "test-secret-key-1234567890abcdef"
        token = _generate_csrf_token(secret, "session1")
        assert not _verify_csrf_token(token, secret, "session2")

    def test_expired_token(self):
        secret = "test-secret-key-1234567890abcdef"
        session_id = "abc123"
        old_timestamp = int(time.time()) - 10000
        token = _generate_csrf_token(secret, session_id, old_timestamp)
        assert not _verify_csrf_token(token, secret, session_id, max_age=7200)

    def test_malformed_token(self):
        secret = "test-secret-key-1234567890abcdef"
        assert not _verify_csrf_token("invalid", secret, "session")
        assert not _verify_csrf_token("abc:def:ghi", secret, "session")
        assert not _verify_csrf_token("", secret, "session")

    def test_token_format(self):
        secret = "test-secret-key-1234567890abcdef"
        session_id = "abc123"
        token = _generate_csrf_token(secret, session_id)
        parts = token.split(":")
        assert len(parts) == 2
        timestamp = int(parts[0])
        assert abs(timestamp - time.time()) < 5
