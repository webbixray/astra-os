"""Approval Use Cases — CRUD for rules, requests, and decisions.

These use cases orchestrate the approval lifecycle:
1. Create rules that define when approval is needed
2. Evaluate rules against action contexts
3. Create requests when rules trigger
4. Record decisions (approve/reject)
5. List pending approvals for the human task queue
6. Expire stale requests
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.common import now
from app.domain.entities.governance.approval import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalRule,
    ApprovalStatus,
    DecisionAction,
    RuleTrigger,
)
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from app.domain.services.governance.approval_service import (
    ApprovalEvaluationResult,
    ApprovalEvaluationService,
)


# ── Repository Port ────────────────────────────────────────────────────


class ApprovalRuleRepository(ABC):
    @abstractmethod
    async def save(self, rule: ApprovalRule) -> ApprovalRule: ...

    @abstractmethod
    async def find_by_id(self, rule_id: UUID) -> ApprovalRule | None: ...

    @abstractmethod
    async def find_by_organization(
        self, org_id: UUID, active_only: bool = True
    ) -> list[ApprovalRule]: ...

    @abstractmethod
    async def delete(self, rule_id: UUID) -> None: ...


class ApprovalRequestRepository(ABC):
    @abstractmethod
    async def save(self, request: ApprovalRequest) -> ApprovalRequest: ...

    @abstractmethod
    async def find_by_id(self, request_id: UUID) -> ApprovalRequest | None: ...

    @abstractmethod
    async def find_pending_by_organization(
        self, org_id: UUID
    ) -> list[ApprovalRequest]: ...

    @abstractmethod
    async def find_pending_by_role(
        self, org_id: UUID, role: str
    ) -> list[ApprovalRequest]: ...

    @abstractmethod
    async def find_expired_stale(self, before: "datetime") -> list[ApprovalRequest]: ...


class ApprovalDecisionRepository(ABC):
    @abstractmethod
    async def save(self, decision: ApprovalDecision) -> ApprovalDecision: ...

    @abstractmethod
    async def find_by_request_id(
        self, request_id: UUID
    ) -> ApprovalDecision | None: ...


# ── Use Cases ──────────────────────────────────────────────────────────


class CreateApprovalRuleUseCase:
    """Create a new approval rule for an organization."""

    def __init__(self, rule_repo: ApprovalRuleRepository):
        self._rule_repo = rule_repo

    async def execute(
        self,
        organization_id: UUID,
        name: str,
        trigger: RuleTrigger,
        conditions: dict[str, Any] | None = None,
        approver_roles: list[str] | None = None,
        priority: int = 0,
        description: str = "",
        approval_timeout_hours: int = 24,
    ) -> ApprovalRule:
        """Create an approval rule.

        Args:
            organization_id: The org this rule belongs to.
            name: Human-readable rule name.
            trigger: What type of action triggers this rule.
            conditions: Trigger-specific conditions (JSON).
            approver_roles: Roles that can approve (default: ["admin"]).
            priority: Higher priority rules evaluated first.
            description: Optional description.
            approval_timeout_hours: Hours before request expires.

        Returns:
            The created ApprovalRule.
        """
        if not name.strip():
            raise ValidationError("Rule name cannot be empty")

        if priority < 0:
            raise ValidationError("Priority must be non-negative")

        # Create using factory methods for specific triggers
        if trigger == RuleTrigger.SPEND_THRESHOLD:
            amount = (conditions or {}).get("min_amount", 0)
            rule = ApprovalRule.create_spend_rule(
                organization_id=organization_id,
                name=name,
                min_amount=amount,
                approver_roles=approver_roles,
            )
        elif trigger == RuleTrigger.BRAND_SENSITIVE:
            keywords = (conditions or {}).get("keywords", [])
            rule = ApprovalRule.create_brand_rule(
                organization_id=organization_id,
                name=name,
                keywords=keywords,
            )
        elif trigger == RuleTrigger.NEW_AUDIENCE:
            rule = ApprovalRule.create_audience_rule(
                organization_id=organization_id,
                name=name,
            )
        else:
            rule = ApprovalRule(
                organization_id=organization_id,
                name=name,
                trigger=trigger,
                conditions=conditions or {},
                approver_roles=approver_roles or ["admin"],
            )

        rule.description = description
        rule.priority = priority
        rule.approval_timeout_hours = approval_timeout_hours

        saved = await self._rule_repo.save(rule)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.APPROVAL_REQUESTED,
                aggregate_id=str(saved.id),
                aggregate_type="approval_rule",
                data={
                    "organization_id": str(organization_id),
                    "name": name,
                    "trigger": trigger.value,
                },
            )
        )

        return saved


class EvaluateApprovalRulesUseCase:
    """Evaluate approval rules against an action context."""

    def __init__(
        self,
        rule_repo: ApprovalRuleRepository,
        evaluation_service: ApprovalEvaluationService | None = None,
    ):
        self._rule_repo = rule_repo
        self._eval_service = evaluation_service or ApprovalEvaluationService()

    async def execute(
        self,
        organization_id: UUID,
        context: dict[str, Any],
    ) -> ApprovalEvaluationResult:
        """Evaluate all active rules for an org against the given context.

        Args:
            organization_id: The org whose rules to evaluate.
            context: Action context (amount, text, channel, etc.)

        Returns:
            EvaluationResult with triggered rules and approval status.
        """
        rules = await self._rule_repo.find_by_organization(
            organization_id, active_only=True
        )
        return self._eval_service.evaluate(rules, context)


class CreateApprovalRequestUseCase:
    """Create an approval request when a rule triggers."""

    def __init__(self, request_repo: ApprovalRequestRepository):
        self._request_repo = request_repo

    async def execute(
        self,
        organization_id: UUID,
        rule: ApprovalRule,
        action_type: str,
        action_resource_id: str,
        action_resource_type: str,
        action_summary: str,
        action_context: dict[str, Any] | None = None,
        triggered_by_agent_id: str | None = None,
        triggered_by_agent_type: str | None = None,
    ) -> ApprovalRequest:
        """Create an approval request.

        Args:
            organization_id: The org this request belongs to.
            rule: The approval rule that triggered this request.
            action_type: Type of action needing approval.
            action_resource_id: ID of the resource.
            action_resource_type: Type of resource.
            action_summary: Human-readable summary of the action.
            action_context: Action details.
            triggered_by_agent_id: Agent that triggered this.
            triggered_by_agent_type: Type of agent.

        Returns:
            The created ApprovalRequest.
        """
        request = ApprovalRequest.create(
            organization_id=organization_id,
            rule=rule,
            action_type=action_type,
            action_resource_id=action_resource_id,
            action_resource_type=action_resource_type,
            action_summary=action_summary,
            action_context=action_context,
            triggered_by_agent_id=triggered_by_agent_id,
            triggered_by_agent_type=triggered_by_agent_type,
        )

        saved = await self._request_repo.save(request)

        await EventBus.publish(
            DomainEvent.create(
                event_type=DomainEventType.APPROVAL_REQUESTED,
                aggregate_id=str(saved.id),
                aggregate_type="approval_request",
                data={
                    "organization_id": str(organization_id),
                    "rule_id": str(rule.id),
                    "rule_name": rule.name,
                    "action_type": action_type,
                    "action_summary": action_summary,
                },
            )
        )

        return saved


class DecideApprovalUseCase:
    """Decide on an approval request (approve/reject)."""

    def __init__(
        self,
        request_repo: ApprovalRequestRepository,
        decision_repo: ApprovalDecisionRepository,
    ):
        self._request_repo = request_repo
        self._decision_repo = decision_repo

    async def execute(
        self,
        request_id: UUID,
        decided_by: UUID,
        action: DecisionAction,
        reason: str = "",
        conditions: dict[str, Any] | None = None,
    ) -> ApprovalDecision:
        """Record a decision on an approval request.

        Args:
            request_id: The approval request to decide on.
            decided_by: The user making the decision.
            action: APPROVE, REJECT, or REQUEST_CHANGES.
            reason: Required for REJECT, optional for others.
            conditions: Optional conditions for approval.

        Returns:
            The recorded ApprovalDecision.

        Raises:
            EntityNotFoundError: If request not found.
            ValidationError: If decision is invalid.
        """
        request = await self._request_repo.find_by_id(request_id)
        if request is None:
            raise EntityNotFoundError("ApprovalRequest", str(request_id))

        # Create the decision
        if action == DecisionAction.APPROVE:
            decision = ApprovalDecision.approve(
                request_id=request_id,
                organization_id=request.organization_id,
                decided_by=decided_by,
                reason=reason,
                conditions=conditions,
            )
            request.approve(decision)

        elif action == DecisionAction.REJECT:
            decision = ApprovalDecision.reject(
                request_id=request_id,
                organization_id=request.organization_id,
                decided_by=decided_by,
                reason=reason,
            )
            request.reject(decision)

        elif action == DecisionAction.REQUEST_CHANGES:
            # Treat like reject but with specific action type
            if not reason:
                raise ValidationError("Reason is required for REQUEST_CHANGES")
            decision = ApprovalDecision.reject(
                request_id=request_id,
                organization_id=request.organization_id,
                decided_by=decided_by,
                reason=reason,
            )
            request.reject(decision)

        elif action == DecisionAction.DELEGATE:
            decision = ApprovalDecision.reject(
                request_id=request_id,
                organization_id=request.organization_id,
                decided_by=decided_by,
                reason=reason or "Delegated",
            )
            request.status = ApprovalStatus.DELEGATED
            request.updated_at = now()

        else:
            raise ValidationError(f"Unknown decision action: {action}")

        # Save both
        await self._request_repo.save(request)
        saved_decision = await self._decision_repo.save(decision)

        # Publish event
        event_type = (
            DomainEventType.APPROVAL_GRANTED
            if action == DecisionAction.APPROVE
            else DomainEventType.APPROVAL_REJECTED
        )
        await EventBus.publish(
            DomainEvent.create(
                event_type=event_type,
                aggregate_id=str(request_id),
                aggregate_type="approval_request",
                data={
                    "organization_id": str(request.organization_id),
                    "action": action.value,
                    "decided_by": str(decided_by),
                    "reason": reason,
                },
            )
        )

        return saved_decision


class ListPendingApprovalsUseCase:
    """List pending approval requests for an organization."""

    def __init__(self, request_repo: ApprovalRequestRepository):
        self._request_repo = request_repo

    async def execute(
        self,
        organization_id: UUID,
        role: str | None = None,
    ) -> list[ApprovalRequest]:
        """List pending approval requests.

        Args:
            organization_id: The org to list requests for.
            role: Optional filter by assigned role.

        Returns:
            List of pending ApprovalRequest objects.
        """
        if role:
            return await self._request_repo.find_pending_by_role(organization_id, role)
        return await self._request_repo.find_pending_by_organization(organization_id)


class ExpireStaleApprovalsUseCase:
    """Expire approval requests that have passed their timeout."""

    def __init__(self, request_repo: ApprovalRequestRepository):
        self._request_repo = request_repo

    async def execute(self) -> list[ApprovalRequest]:
        """Find and expire all stale approval requests.

        Returns:
            List of expired ApprovalRequest objects.
        """
        stale = await self._request_repo.find_expired_stale(now())
        expired: list[ApprovalRequest] = []

        for request in stale:
            if request.is_pending:
                request.expire()
                await self._request_repo.save(request)
                expired.append(request)

                await EventBus.publish(
                    DomainEvent.create(
                        event_type=DomainEventType.APPROVAL_REJECTED,
                        aggregate_id=str(request.id),
                        aggregate_type="approval_request",
                        data={
                            "organization_id": str(request.organization_id),
                            "action": "expired",
                            "rule_name": request.rule_name,
                        },
                    )
                )

        return expired
