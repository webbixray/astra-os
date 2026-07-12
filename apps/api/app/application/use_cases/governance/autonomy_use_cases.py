"""Autonomy Use Cases — config management, action checking, explainability.

These use cases wrap the autonomy and explainability domain services with
persistence and event publishing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.common import now
from app.domain.entities.governance.autonomy import (
    AgentAction,
    AutonomyConfig,
    AutonomyLevel,
)
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from app.domain.services.governance.approval_service import ApprovalEvaluationService
from app.domain.services.governance.autonomy_enforcement import (
    AutonomyEnforcementService,
    EnforcementResult,
)
from app.domain.services.governance.explainability import (
    ExplainabilityService,
    ExplanationOutput,
)


# ── Repository Ports ──────────────────────────────────────────────────


class AutonomyConfigRepository(ABC):
    @abstractmethod
    async def save(self, config: AutonomyConfig) -> AutonomyConfig: ...

    @abstractmethod
    async def find_by_organization(self, org_id: UUID) -> AutonomyConfig | None: ...


class AgentActionRepository(ABC):
    @abstractmethod
    async def save(self, action: AgentAction) -> AgentAction: ...

    @abstractmethod
    async def find_by_id(self, action_id: UUID) -> AgentAction | None: ...

    @abstractmethod
    async def find_by_organization(
        self,
        org_id: UUID,
        agent_type: str | None = None,
        action_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentAction]: ...

    @abstractmethod
    async def find_by_agent(
        self,
        org_id: UUID,
        agent_id: str,
        limit: int = 50,
    ) -> list[AgentAction]: ...


# ── Use Cases ──────────────────────────────────────────────────────────


class GetAutonomyConfigUseCase:
    """Get the autonomy configuration for an organization."""

    def __init__(self, config_repo: AutonomyConfigRepository):
        self._config_repo = config_repo

    async def execute(self, organization_id: UUID) -> AutonomyConfig:
        """Get or create the default autonomy config for an org."""
        config = await self._config_repo.find_by_organization(organization_id)
        if config is None:
            # Create default config (ADVISORY for everything)
            config = AutonomyConfig.create(
                organization_id=organization_id,
                default_level=AutonomyLevel.ADVISORY,
            )
            config = await self._config_repo.save(config)
        return config


class UpdateAutonomyConfigUseCase:
    """Update the autonomy configuration for an organization."""

    def __init__(self, config_repo: AutonomyConfigRepository):
        self._config_repo = config_repo

    async def execute(
        self,
        organization_id: UUID,
        default_level: AutonomyLevel | None = None,
        agent_levels: dict[str, AutonomyLevel] | None = None,
        action_overrides: dict[str, AutonomyLevel] | None = None,
        auto_approve_spend_limit: float | None = None,
        auto_execute_channels: list[str] | None = None,
    ) -> AutonomyConfig:
        """Update autonomy configuration.

        Only provided fields are updated (partial update).
        """
        config = await self._config_repo.find_by_organization(organization_id)
        if config is None:
            raise EntityNotFoundError("AutonomyConfig", str(organization_id))

        if default_level is not None:
            config.default_level = default_level

        if agent_levels is not None:
            config.agent_levels = agent_levels

        if action_overrides is not None:
            config.action_overrides = action_overrides

        if auto_approve_spend_limit is not None:
            if auto_approve_spend_limit < 0:
                raise ValidationError("Spend limit cannot be negative")
            config.auto_approve_spend_limit = auto_approve_spend_limit

        if auto_execute_channels is not None:
            config.auto_execute_channels = auto_execute_channels

        config.updated_at = now()
        saved = await self._config_repo.save(config)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.ORGANIZATION_UPDATED,
                aggregate_id=str(organization_id),
                aggregate_type="autonomy_config",
                data={
                    "organization_id": str(organization_id),
                    "default_level": saved.default_level.value,
                },
            )
        )

        return saved


class CheckAgentActionUseCase:
    """Check whether an agent action is permitted before execution.

    This is the primary entry point called by agents before executing
    any action. It combines autonomy config + approval rules to determine
    if the action can proceed.
    """

    def __init__(
        self,
        config_repo: AutonomyConfigRepository,
        enforcement_service: AutonomyEnforcementService | None = None,
    ):
        self._config_repo = config_repo
        self._enforcement = enforcement_service or AutonomyEnforcementService()

    async def execute(
        self,
        organization_id: UUID,
        action_name: str,
        agent_type: str,
        agent_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        context: dict[str, Any] | None = None,
        spend_amount: float = 0.0,
    ) -> EnforcementResult:
        """Check if an agent action is permitted.

        Args:
            organization_id: The org context.
            action_name: Action identifier (e.g., "campaign.launch").
            agent_type: Type of agent (e.g., "AdvertisingDirector").
            agent_id: Unique agent ID.
            resource_type: Type of resource being acted on.
            resource_id: ID of the resource.
            context: Additional context for rule evaluation.
            spend_amount: Amount of money involved (if any).

        Returns:
            EnforcementResult with allowed/required approval info.
        """
        config = await self._config_repo.find_by_organization(organization_id)
        if config is None:
            # Default to ADVISORY — everything requires approval
            config = AutonomyConfig.create(organization_id=organization_id)
            config = await self._config_repo.save(config)

        action = AgentAction.create(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action_name,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        if spend_amount > 0:
            action.details["amount"] = spend_amount

        # Check with no approval rules for now (rules added at API layer)
        result = self._enforcement.check(
            config=config,
            rules=[],
            action=action,
            agent_type=agent_type,
            context=context,
        )

        return result


class RecordAgentActionUseCase:
    """Record an agent action for audit and explainability."""

    def __init__(self, action_repo: AgentActionRepository):
        self._action_repo = action_repo

    async def execute(
        self,
        organization_id: UUID,
        agent_id: str,
        agent_type: str,
        action_name: str,
        resource_type: str = "",
        resource_id: str = "",
        reasoning: str = "",
        reasoning_trace: list[dict[str, Any]] | None = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.ADVISORY,
        was_auto_executed: bool = False,
        approval_request_id: UUID | None = None,
        success: bool = True,
        error_message: str = "",
        result: dict[str, Any] | None = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        model_used: str = "",
        details: dict[str, Any] | None = None,
    ) -> AgentAction:
        """Record an agent action.

        Creates an immutable audit record of what the agent did, why,
        and what happened.
        """
        agent_action = AgentAction.create(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action_name,
            resource_type=resource_type,
            resource_id=resource_id,
            reasoning=reasoning,
        )

        if reasoning_trace:
            agent_action.reasoning_trace = reasoning_trace

        agent_action.autonomy_level = autonomy_level
        agent_action.was_auto_executed = was_auto_executed
        agent_action.approval_request_id = approval_request_id
        agent_action.success = success
        agent_action.error_message = error_message
        agent_action.result = result or {}
        agent_action.tokens_used = tokens_used
        agent_action.cost_usd = cost_usd
        agent_action.model_used = model_used
        agent_action.details = details or {}

        saved = await self._action_repo.save(agent_action)

        # Publish event
        event_type = (
            DomainEventType.AI_AGENT_TASK_COMPLETED
            if success
            else DomainEventType.AI_AGENT_TASK_FAILED
        )
        await EventBus.publish(
            DomainEvent.create(
                event_type=event_type,
                aggregate_id=str(saved.id),
                aggregate_type="agent_action",
                data={
                    "organization_id": str(organization_id),
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "action": action_name,
                    "success": success,
                },
            )
        )

        return saved


class GetAgentActionsUseCase:
    """Query agent actions for audit/explainability."""

    def __init__(self, action_repo: AgentActionRepository):
        self._action_repo = action_repo

    async def execute(
        self,
        organization_id: UUID,
        agent_type: str | None = None,
        action_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentAction]:
        """List agent actions for an organization."""
        return await self._action_repo.find_by_organization(
            organization_id,
            agent_type=agent_type,
            action_name=action_name,
            limit=limit,
            offset=offset,
        )

    async def get_by_id(self, action_id: UUID) -> AgentAction:
        """Get a specific agent action by ID."""
        action = await self._action_repo.find_by_id(action_id)
        if action is None:
            raise EntityNotFoundError("AgentAction", str(action_id))
        return action


class GetExplainabilityReportUseCase:
    """Generate explainability reports for agent actions."""

    def __init__(
        self,
        action_repo: AgentActionRepository,
        explainability_service: ExplainabilityService | None = None,
    ):
        self._action_repo = action_repo
        self._explainability = explainability_service or ExplainabilityService()

    async def explain_action(self, action_id: UUID) -> ExplanationOutput:
        """Generate a full explanation for a specific action."""
        action = await self._action_repo.find_by_id(action_id)
        if action is None:
            raise EntityNotFoundError("AgentAction", str(action_id))
        return self._explainability.explain(action)

    async def explain_actions(
        self,
        organization_id: UUID,
        agent_type: str | None = None,
        limit: int = 50,
    ) -> list[ExplanationOutput]:
        """Explain multiple actions for an organization."""
        actions = await self._action_repo.find_by_organization(
            organization_id,
            agent_type=agent_type,
            limit=limit,
        )
        return [self._explainability.explain(a) for a in actions]

    async def generate_summary(
        self,
        action_id: UUID,
    ) -> str:
        """One-line summary of an action."""
        action = await self._action_repo.find_by_id(action_id)
        if action is None:
            raise EntityNotFoundError("AgentAction", str(action_id))
        return self._explainability.generate_summary(action)

    async def replay_decision(self, action_id: UUID) -> list[dict[str, Any]]:
        """Step-by-step decision replay."""
        action = await self._action_repo.find_by_id(action_id)
        if action is None:
            raise EntityNotFoundError("AgentAction", str(action_id))
        return self._explainability.replay_decision(action)

    async def generate_audit_summary(
        self,
        organization_id: UUID,
    ) -> dict[str, Any]:
        """Audit summary for all actions in an org."""
        actions = await self._action_repo.find_by_organization(
            organization_id,
            limit=1000,
        )
        return self._explainability.generate_audit_summary(
            actions, organization_id
        )
