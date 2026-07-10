from __future__ import annotations

import logging

from app.domain.events.event_bus import DomainEvent, DomainEventType, event_handler
from app.infrastructure.metrics import workflows_completed, workflows_failed

logger = logging.getLogger(__name__)


@event_handler(DomainEventType.CAMPAIGN_CREATED)
async def on_campaign_created(event: DomainEvent) -> None:
    logger.info("Campaign created: %s (org: %s)", event.aggregate_id, event.data.get("organization_id"))


@event_handler(DomainEventType.CAMPAIGN_ACTIVATED)
async def on_campaign_activated(event: DomainEvent) -> None:
    logger.info("Campaign activated: %s", event.aggregate_id)


@event_handler(DomainEventType.CAMPAIGN_COMPLETED)
async def on_campaign_completed(event: DomainEvent) -> None:
    logger.info("Campaign completed: %s", event.aggregate_id)


@event_handler(DomainEventType.CONTENT_PUBLISHED)
async def on_content_published(event: DomainEvent) -> None:
    logger.info(
        "Content published: %s (type: %s, platform: %s)",
        event.aggregate_id,
        event.data.get("content_type"),
        event.data.get("platform"),
    )


@event_handler(DomainEventType.WORKFLOW_COMPLETED)
async def on_workflow_completed(event: DomainEvent) -> None:
    workflows_completed.inc()
    logger.info("Workflow completed: %s (%d steps)", event.aggregate_id, len(event.data.get("steps", [])))


@event_handler(DomainEventType.WORKFLOW_FAILED)
async def on_workflow_failed(event: DomainEvent) -> None:
    workflows_failed.inc()
    logger.warning(
        "Workflow failed: %s (error: %s)",
        event.aggregate_id,
        event.data.get("error"),
    )


@event_handler(DomainEventType.APPROVAL_REQUESTED)
async def on_approval_requested(event: DomainEvent) -> None:
    logger.info(
        "Approval required: %s (type: %s, requested_by: %s)",
        event.aggregate_id,
        event.data.get("approval_type"),
        event.data.get("requested_by"),
    )


@event_handler(DomainEventType.USER_SIGNED_IN)
async def on_user_signed_in(event: DomainEvent) -> None:
    logger.info("User signed in: %s", event.aggregate_id)


@event_handler(DomainEventType.USER_SIGNED_UP)
async def on_user_signed_up(event: DomainEvent) -> None:
    logger.info("New user registered: %s (%s)", event.aggregate_id, event.data.get("email"))


@event_handler(DomainEventType.ORGANIZATION_CREATED)
async def on_organization_created(event: DomainEvent) -> None:
    logger.info("Organization created: %s (%s)", event.aggregate_id, event.data.get("name"))


@event_handler(DomainEventType.AD_ACCOUNT_CONNECTED)
async def on_ad_account_connected(event: DomainEvent) -> None:
    logger.info(
        "Ad account connected: %s (platform: %s)",
        event.aggregate_id,
        event.data.get("platform"),
    )


@event_handler(DomainEventType.BILLING_PLAN_CHANGED)
async def on_billing_plan_changed(event: DomainEvent) -> None:
    logger.info(
        "Billing plan changed: org=%s, plan=%s → %s",
        event.aggregate_id,
        event.data.get("previous_plan"),
        event.data.get("new_plan"),
    )


@event_handler(DomainEventType.EMAIL_BOUNCED)
async def on_email_bounced(event: DomainEvent) -> None:
    logger.warning(
        "Email bounced: campaign=%s, recipient=%s",
        event.data.get("campaign_id"),
        event.data.get("recipient"),
    )


@event_handler(DomainEventType.AI_CONTENT_GENERATED)
async def on_ai_content_generated(event: DomainEvent) -> None:
    logger.info(
        "AI content generated: type=%s, length=%d chars",
        event.data.get("content_type"),
        len(event.data.get("content", "") or ""),
    )
