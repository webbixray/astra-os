"""Casbin enforcer for RBAC."""

import logging
from pathlib import Path

import casbin
import casbin_async_sqlalchemy_adapter

from app.config import config

logger = logging.getLogger(__name__)

# Global enforcer instance
_enforcer: casbin.AsyncEnforcer | None = None


# Default policy model for Casbin
MODEL_CONF = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
"""


async def init_enforcer() -> casbin.AsyncEnforcer:
    """Initialize Casbin enforcer with database adapter."""
    global _enforcer

    if _enforcer is not None:
        return _enforcer

    # Use database adapter if database URL is available
    if config.database_url:
        try:
            adapter = casbin_async_sqlalchemy_adapter.Adapter(config.database_url)
            _enforcer = casbin.AsyncEnforcer(MODEL_CONF, adapter)
            await _enforcer.load_policy()
            logger.info("Casbin enforcer initialized with database adapter")
        except Exception as e:
            logger.warning("Failed to init Casbin with DB adapter, falling back to file: %s", e)
            _enforcer = await _init_file_enforcer()
    else:
        _enforcer = await _init_file_enforcer()

    # Add default policies if none exist
    await _ensure_default_policies()

    return _enforcer


async def _init_file_enforcer() -> casbin.AsyncEnforcer:
    """Initialize Casbin enforcer with file-based policy storage."""
    policy_file = Path("config/casbin_policy.csv")
    policy_file.parent.mkdir(parents=True, exist_ok=True)

    if not policy_file.exists():
        policy_file.write_text("p, sub, obj, act\n")

    enforcer = casbin.AsyncEnforcer(MODEL_CONF, str(policy_file))
    await enforcer.load_policy()
    logger.info("Casbin enforcer initialized with file adapter: %s", policy_file)
    return enforcer


async def _ensure_default_policies() -> None:
    """Ensure default RBAC policies are loaded."""
    if _enforcer is None:
        return

    # Check if policies already exist
    policies = await _enforcer.get_policy()
    if policies:
        return

    # Default RBAC policies
    # Format: role, resource, action
    default_policies = [
        # Owner - full access to everything
        ["owner", "organizations", "*"],
        ["owner", "campaigns", "*"],
        ["owner", "content", "*"],
        ["owner", "agents", "*"],
        ["owner", "workflows", "*"],
        ["owner", "analytics", "*"],
        ["owner", "knowledge", "*"],
        ["owner", "advertising", "*"],
        ["owner", "email", "*"],
        ["owner", "reports", "*"],
        ["owner", "notifications", "*"],
        ["owner", "dashboards", "*"],
        ["owner", "teams", "*"],
        ["owner", "users", "*"],
        ["owner", "settings", "*"],
        # Admin - full access except organization-level settings
        ["admin", "organizations", "read"],
        ["admin", "campaigns", "*"],
        ["admin", "content", "*"],
        ["admin", "agents", "*"],
        ["admin", "workflows", "*"],
        ["admin", "analytics", "*"],
        ["admin", "knowledge", "*"],
        ["admin", "advertising", "*"],
        ["admin", "email", "*"],
        ["admin", "reports", "*"],
        ["admin", "notifications", "*"],
        ["admin", "dashboards", "*"],
        ["admin", "teams", "read"],
        ["admin", "teams", "write"],
        ["admin", "users", "read"],
        ["admin", "users", "write"],
        # Operator - operational access
        ["operator", "organizations", "read"],
        ["operator", "campaigns", "read"],
        ["operator", "campaigns", "write"],
        ["operator", "content", "read"],
        ["operator", "content", "write"],
        ["operator", "agents", "read"],
        ["operator", "workflows", "read"],
        ["operator", "workflows", "write"],
        ["operator", "analytics", "read"],
        ["operator", "knowledge", "read"],
        ["operator", "advertising", "read"],
        ["operator", "email", "read"],
        ["operator", "reports", "read"],
        ["operator", "notifications", "read"],
        ["operator", "dashboards", "read"],
        # Viewer - read-only access
        ["viewer", "organizations", "read"],
        ["viewer", "campaigns", "read"],
        ["viewer", "content", "read"],
        ["operator", "agents", "read"],
        ["viewer", "workflows", "read"],
        ["viewer", "analytics", "read"],
        ["viewer", "knowledge", "read"],
        ["viewer", "advertising", "read"],
        ["viewer", "email", "read"],
        ["viewer", "reports", "read"],
        ["viewer", "notifications", "read"],
        ["viewer", "dashboards", "read"],
    ]

    await _enforcer.add_policies(default_policies)
    await _enforcer.save_policy()
    logger.info("Loaded %d default Casbin policies", len(default_policies))


def get_enforcer() -> casbin.AsyncEnforcer:
    """Get the global Casbin enforcer instance."""
    if _enforcer is None:
        raise RuntimeError("Casbin enforcer not initialized. Call init_enforcer() first.")
    return _enforcer


async def add_user_role(user_id: str, role: str) -> None:
    """Assign a role to a user."""
    enforcer = get_enforcer()
    await enforcer.add_grouping_policy(user_id, role)
    await enforcer.save_policy()


async def remove_user_role(user_id: str, role: str) -> None:
    """Remove a role from a user."""
    enforcer = get_enforcer()
    await enforcer.remove_grouping_policy(user_id, role)
    await enforcer.save_policy()


async def get_user_roles(user_id: str) -> list[str]:
    """Get all roles assigned to a user."""
    enforcer = get_enforcer()
    return await enforcer.get_roles_for_user(user_id)


async def add_permission(role: str, resource: str, action: str) -> None:
    """Add a permission to a role."""
    enforcer = get_enforcer()
    await enforcer.add_policy(role, resource, action)
    await enforcer.save_policy()


async def remove_permission(role: str, resource: str, action: str) -> None:
    """Remove a permission from a role."""
    enforcer = get_enforcer()
    await enforcer.remove_policy(role, resource, action)
    await enforcer.save_policy()
