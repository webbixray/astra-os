"""SQLAlchemy custom types for transparent field-level encryption."""

from __future__ import annotations

from sqlalchemy import String, Text, TypeDecorator

from app.infrastructure.security.encryption import (
    decrypt_field,
    encrypt_field,
    get_secret_key,
)


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that encrypts on write and decrypts on read.

    Usage::

        api_key: Mapped[str] = mapped_column(EncryptedString(255), nullable=False)
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int | None = None, *args, **kwargs):
        super().__init__(length or 2048, *args, **kwargs)

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_field(value, get_secret_key())

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_field(value, get_secret_key())


class EncryptedText(TypeDecorator):
    """SQLAlchemy type for encrypting large text fields (JSON blobs, etc.)."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_field(value, get_secret_key())

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_field(value, get_secret_key())


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type for encrypting a JSON-serializable dict.

    The dict is serialized to a JSON string, encrypted, then stored as Text.
    On read, it is decrypted and parsed back to a dict.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: dict | None, dialect) -> str | None:
        if value is None:
            return None
        import json

        plaintext = json.dumps(value, default=str)
        return encrypt_field(plaintext, get_secret_key())

    def process_result_value(self, value: str | None, dialect) -> dict | None:
        if value is None:
            return None
        import json

        plaintext = decrypt_field(value, get_secret_key())
        return json.loads(plaintext)
