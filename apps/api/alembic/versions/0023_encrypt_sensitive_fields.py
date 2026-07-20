"""Encrypt sensitive fields: email_providers.api_key and ad_accounts.credentials.

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-10
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def _encrypt(plaintext: str, secret_key: str) -> str:
    """Encrypt using the application's stdlib-only encryption."""
    from app.infrastructure.security.encryption import encrypt_field

    return encrypt_field(plaintext, secret_key)


def upgrade() -> None:
    import os

    secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-in-production")
    conn = op.get_bind()

    # Encrypt email_providers.api_key (skip already encrypted)
    rows = conn.execute(
        text("SELECT id, api_key FROM email_providers WHERE api_key NOT LIKE 'ENC$v1$%'")
    ).fetchall()
    for row in rows:
        encrypted = _encrypt(row.api_key, secret_key)
        conn.execute(
            text("UPDATE email_providers SET api_key = :val WHERE id = :id"),
            {"val": encrypted, "id": row.id},
        )

    # Widen api_key column for encrypted values
    op.alter_column("email_providers", "api_key", type_=sa.Text(), nullable=False)

    # Encrypt ad_accounts.credentials
    rows = conn.execute(text("SELECT id, credentials FROM ad_accounts")).fetchall()
    for row in rows:
        creds = row.credentials
        if creds and isinstance(creds, dict):
            import json

            plaintext = json.dumps(creds, default=str)
            encrypted = _encrypt(plaintext, secret_key)
            conn.execute(
                text("UPDATE ad_accounts SET credentials = :val WHERE id = :id"),
                {"val": encrypted, "id": row.id},
            )

    # Change credentials column to Text for encrypted storage
    op.alter_column("ad_accounts", "credentials", type_=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column("email_providers", "api_key", type_=sa.Text(), nullable=False)
    op.alter_column("ad_accounts", "credentials", type_=sa.JSON(), nullable=True)
