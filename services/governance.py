"""Governance submodule for services package - delegates to astra_agent_orchestrator.governance."""

from astra_agent_orchestrator.governance import (
    GovernanceMiddleware,
    GovernanceCheckResult,
)

__all__ = [
    "GovernanceMiddleware",
    "GovernanceCheckResult",
]
