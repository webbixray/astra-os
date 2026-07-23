"""Field-level encryption utilities using stdlib-only HMAC + XOR stream cipher.

Provides transparent encrypt/decrypt for sensitive database fields.
Encrypted values are prefixed with ``ENC$v1$`` so we can detect
already-encrypted data and support key rotation in the future.

Encryption scheme:
  - AES-like CTR mode using SHA-256 as the block function
  - HMAC-SHA256 for authentication (encrypt-then-MAC)
  - 16-byte random nonce per encryption

This is a stdlib-only implementation (no ``cryptography`` package required).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import struct

_PREFIX = "ENC$v1$"
_NONCE_LEN = 16
_BLOCK_SIZE = 32  # SHA-256 output
logger = logging.getLogger(__name__)


def _derive_keys(secret_key: str) -> tuple[bytes, bytes]:
    """Derive encryption key and MAC key from the application secret."""
    enc_key = hashlib.pbkdf2_hmac("sha256", secret_key.encode(), b"astra-enc-v1", 100_000, dklen=32)
    mac_key = hashlib.pbkdf2_hmac("sha256", secret_key.encode(), b"astra-mac-v1", 100_000, dklen=32)
    return enc_key, mac_key


def _xor_crypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    """CTR-mode XOR stream cipher using SHA-256 as the block function."""
    out = bytearray()
    counter = 0
    while len(out) < len(data):
        block_key = hashlib.sha256(
            key + struct.pack(">QQ", int.from_bytes(nonce[:8], "big"), counter)
        ).digest()
        chunk = data[len(out) : len(out) + _BLOCK_SIZE]
        out.extend(bytes(a ^ b for a, b in zip(chunk, block_key[: len(chunk)], strict=True)))
        counter += 1
    return bytes(out)


def encrypt_field(plaintext: str, secret_key: str) -> str:
    """Encrypt a plaintext string. Returns a prefixed token safe for DB storage."""
    if not plaintext:
        return plaintext
    if plaintext.startswith(_PREFIX):
        return plaintext

    enc_key, mac_key = _derive_keys(secret_key)
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = _xor_crypt(plaintext.encode("utf-8"), enc_key, nonce)
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()

    payload = nonce + ciphertext + tag
    token = base64.urlsafe_b64encode(payload).decode("ascii")
    return f"{_PREFIX}{token}"


def decrypt_field(ciphertext: str, secret_key: str) -> str:
    """Decrypt a prefixed token back to plaintext.

    If the value is not prefixed (legacy plaintext), it is returned as-is
    so reads continue to work during migration.
    """
    if not ciphertext:
        return ciphertext
    if not ciphertext.startswith(_PREFIX):
        return ciphertext

    enc_key, mac_key = _derive_keys(secret_key)
    try:
        payload = base64.urlsafe_b64decode(ciphertext[len(_PREFIX) :])
    except Exception:
        logger.warning("Failed to decode encrypted field payload (corrupt base64)")
        return ciphertext

    if len(payload) < _NONCE_LEN + 1 + 32:
        logger.warning("Encrypted field payload too short (%d bytes)", len(payload))
        return ciphertext

    nonce = payload[:_NONCE_LEN]
    tag = payload[-32:]
    encrypted_data = payload[_NONCE_LEN:-32]

    expected_tag = hmac.new(mac_key, nonce + encrypted_data, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        logger.warning("Encrypted field HMAC verification failed (wrong key or tampered data)")
        return ciphertext

    plaintext = _xor_crypt(encrypted_data, enc_key, nonce)
    return plaintext.decode("utf-8", errors="replace")


def is_encrypted(value: str) -> bool:
    return bool(value and value.startswith(_PREFIX))


def get_secret_key() -> str:
    """Return the current application secret key."""
    from app.config import config

    return config.secret_key
