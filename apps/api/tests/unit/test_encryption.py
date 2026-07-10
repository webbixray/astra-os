from app.infrastructure.security.encryption import (
    decrypt_field,
    encrypt_field,
    is_encrypted,
)

SECRET = "test-secret-key-that-is-long-enough-for-fernet-1234567890"


class TestEncryptDecrypt:
    def test_round_trip(self):
        original = "sk-1234567890abcdef"
        encrypted = encrypt_field(original, SECRET)
        assert encrypted != original
        assert is_encrypted(encrypted)
        assert decrypt_field(encrypted, SECRET) == original

    def test_empty_string_passthrough(self):
        assert encrypt_field("", SECRET) == ""
        assert decrypt_field("", SECRET) == ""

    def test_not_double_encrypted(self):
        first = encrypt_field("secret", SECRET)
        second = encrypt_field(first, SECRET)
        assert first == second

    def test_plaintext_passthrough_on_decrypt(self):
        legacy = "sk-plaintext-key"
        assert decrypt_field(legacy, SECRET) == legacy

    def test_different_keys_fail(self):
        encrypted = encrypt_field("secret", SECRET)
        result = decrypt_field(encrypted, "wrong-key-1234567890abcdefghijklmnop")
        assert result == encrypted

    def test_is_encrypted(self):
        assert is_encrypted(encrypt_field("x", SECRET))
        assert not is_encrypted("plaintext")
        assert not is_encrypted("")
        assert not is_encrypted(None)
