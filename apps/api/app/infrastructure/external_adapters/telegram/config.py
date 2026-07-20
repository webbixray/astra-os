"""Telegram Bot Configuration for Astra OS"""

from pydantic_settings import BaseSettings
from pydantic import Field


class TelegramConfig(BaseSettings):
    """Configuration for Telegram Bot integration."""

    # Bot token from BotFather
    bot_token: str = Field(
        default="",
        description="Telegram Bot API token from BotFather",
    )

    # Webhook URL for production
    webhook_url: str = Field(
        default="",
        description="Public HTTPS URL for webhook (production)",
    )

    # Webhook path
    webhook_path: str = Field(
        default="/api/v1/telegram/webhook",
        description="Path for webhook endpoint",
    )

    # Polling mode (development)
    use_polling: bool = Field(
        default=True,
        description="Use long polling instead of webhook (development)",
    )

    # Allowed users (comma-separated user IDs)
    allowed_user_ids: str = Field(
        default="",
        description="Comma-separated list of allowed Telegram user IDs",
    )

    # Allowed chat IDs (comma-separated)
    allowed_chat_ids: str = Field(
        default="",
        description="Comma-separated list of allowed Telegram chat IDs",
    )

    # Admin user IDs (can access all commands)
    admin_user_ids: str = Field(
        default="",
        description="Comma-separated list of admin Telegram user IDs",
    )

    # Session timeout (minutes)
    session_timeout_minutes: int = Field(
        default=30,
        description="User session timeout in minutes",
    )

    # Command prefix
    command_prefix: str = Field(
        default="/",
        description="Command prefix character",
    )

    # Parse mode
    parse_mode: str = Field(
        default="HTML",
        description="Message parse mode (HTML or Markdown)",
    )

    # Request timeout
    request_timeout: int = Field(
        default=30,
        description="Telegram API request timeout in seconds",
    )

    # Retry settings
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests",
    )

    retry_delay: float = Field(
        default=1.0,
        description="Delay between retries in seconds",
    )

    # Webhook secret token for validation
    webhook_secret_token: str = Field(
        default="",
        description="Secret token for webhook validation (set in BotFather)",
    )

    # Redis URL for FSM storage and session persistence
    redis_url: str = Field(
        default="",
        description="Redis URL for FSM storage and session persistence",
    )

    class Config:
        env_prefix = "TELEGRAM_"
        case_sensitive = False


# Singleton instance
_config: TelegramConfig | None = None


def get_telegram_config() -> TelegramConfig:
    """Get the Telegram configuration singleton."""
    global _config
    if _config is None:
        _config = TelegramConfig()
    return _config


def reset_telegram_config() -> None:
    """Reset the configuration (useful for testing)."""
    global _config
    _config = None
