"""Configuration and authentication modules for Astra CLI"""

from pathlib import Path
from typing import Any

import yaml

# Config file paths
CONFIG_DIR = Path.home() / ".astra"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.yaml"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from file"""
    path = config_path or CONFIG_FILE
    if not path.exists():
        return get_default_config()

    with open(path) as f:
        return yaml.safe_load(f) or get_default_config()


def get_default_config() -> dict[str, Any]:
    """Get default configuration"""
    return {
        "api": {
            "url": "https://api.astra-os.io",
            "timeout": 30,
        },
        "auth": {
            "token": None,
            "refresh_token": None,
        },
        "defaults": {
            "organization": None,
            "project": None,
            "output_format": "table",
        },
        "monitoring": {
            "enabled": True,
            "interval": 60,
        },
    }


def save_config(config: dict[str, Any], config_path: Path | None = None) -> None:
    """Save configuration to file"""
    path = config_path or CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_config_value(
    key: str, config: dict[str, Any] | None = None, config_path: Path | None = None
) -> Any:
    """Get a configuration value by dot-notation key (e.g., 'api.url')"""
    if config is None:
        config = load_config(config_path)
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return None
    return value


def set_config_value(
    key: str, value: Any, config: dict[str, Any] | None = None, config_path: Path | None = None
) -> dict[str, Any]:
    """Set a configuration value by dot-notation key"""
    if config is None:
        config = load_config(config_path)
    keys = key.split(".")

    # Navigate to parent
    target = config
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    # Set value
    target[keys[-1]] = value
    if config_path:
        save_config(config, config_path)
    return config


def load_credentials() -> dict[str, Any]:
    """Load credentials from file"""
    if not CREDENTIALS_FILE.exists():
        return {}

    with open(CREDENTIALS_FILE) as f:
        return yaml.safe_load(f) or {}


def save_credentials(credentials: dict[str, Any]) -> None:
    """Save credentials to file"""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        yaml.dump(credentials, f, default_flow_style=False)

    # Set restrictive permissions
    CREDENTIALS_FILE.chmod(0o600)


def get_token() -> str | None:
    """Get current auth token"""
    config = load_config()
    return config.get("auth", {}).get("token")


def get_refresh_token() -> str | None:
    """Get current refresh token"""
    config = load_config()
    return config.get("auth", {}).get("refresh_token")


def set_tokens(access_token: str, refresh_token: str | None = None) -> None:
    """Set auth tokens in config"""
    config = load_config()
    config.setdefault("auth", {})
    config["auth"]["token"] = access_token
    if refresh_token:
        config["auth"]["refresh_token"] = refresh_token
    save_config(config)


def clear_tokens() -> None:
    """Clear auth tokens"""
    config = load_config()
    config.setdefault("auth", {})
    config["auth"]["token"] = None
    config["auth"]["refresh_token"] = None
    save_config(config)


def get_credentials() -> dict[str, Any]:
    """Load credentials from file"""
    if not CREDENTIALS_FILE.exists():
        return {}

    with open(CREDENTIALS_FILE) as f:
        return yaml.safe_load(f) or {}


def save_credentials(credentials: dict[str, Any]) -> None:
    """Save credentials to file"""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        yaml.dump(credentials, f, default_flow_style=False)

    # Set restrictive permissions
    CREDENTIALS_FILE.chmod(0o600)


def get_api_url(config: dict[str, Any]) -> str:
    """Get API URL from config"""
    return config.get("api", {}).get("url", "https://api.astra-os.io")


def get_api_token(config: dict[str, Any]) -> str | None:
    """Get API token from config"""
    return config.get("auth", {}).get("token")


def set_api_token(config: dict[str, Any], token: str) -> None:
    """Set API token in config"""
    config.setdefault("auth", {})
    config["auth"]["token"] = token
