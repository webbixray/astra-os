import asyncio
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.notifications.notification_hub_service import NotificationHubService
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.db.repositories.notification_repository import NotificationRepository
from app.infrastructure.db.repositories.notifications.announcement_repository import (
    AnnouncementRepository,
)
from app.infrastructure.db.repositories.notifications.preference_repository import (
    PreferenceRepository,
)
from app.infrastructure.db.repositories.notifications.template_repository import (
    NotificationTemplateRepository,
)
from app.presentation.dependencies import get_db, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import PaginatedResponse

router = APIRouter()


class SendNotificationRequest(BaseModel):
    organization_id: UUID
    user_id: UUID
    type: str
    title: str
    body: str = ""
    resource_type: str = ""
    resource_id: str = ""
    channel: str = "in_app"


class SendFromTemplateRequest(BaseModel):
    organization_id: UUID
    user_id: UUID
    template_id: UUID
    variables: dict = {}
    resource_type: str = ""
    resource_id: str = ""


class CreateTemplateRequest(BaseModel):
    name: str
    type: str = "general"
    channel: str = "in_app"
    title_template: str
    body_template: str = ""
    variables: list[str] = []


class SetPreferenceRequest(BaseModel):
    notification_type: str
    channel: str
    enabled: bool = True


class CreateAnnouncementRequest(BaseModel):
    title: str
    body: str = ""
    severity: str = "info"
    target_role: str = ""
    expires_at: datetime | None = None


def get_service(db: AsyncSession = Depends(get_db)) -> NotificationHubService:
    return NotificationHubService(
        notif_repo=NotificationRepository(db),
        template_repo=NotificationTemplateRepository(db),
        pref_repo=PreferenceRepository(db),
        announcement_repo=AnnouncementRepository(db),
    )


# ── SSE Stream ──────────────────────────────────────────────────────────────

@router.get("/notifications/stream", summary="Stream notifications via SSE")
async def stream_notifications(
    user_id: UUID = Depends(require_user_id),
    service: NotificationHubService = Depends(get_service),
) -> StreamingResponse:
    queue = service.subscribe(user_id)

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            service.unsubscribe(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Notifications ────────────────────────────────────────────────────────────

@router.get("/notifications", summary="List notifications")
async def list_notifications(
    organization_id: UUID = Query(...),
    unread_only: bool = Query(default=False),
    channel: str | None = Query(default=None),
    archived: bool = Query(default=False),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    page = pagination["page"]
    limit = pagination["limit"]
    offset = (page - 1) * limit
    result = await service.list_notifications(
        user_id=user_id, organization_id=organization_id,
        unread_only=unread_only, channel=channel,
        archived=archived, limit=limit, offset=offset,
    )
    return PaginatedResponse(
        data=result["items"],
        total=result["total"],
        page=page,
        limit=limit,
        pages=max(1, (result["total"] + limit - 1) // limit),
    )


@router.get("/notifications/unread-count", summary="Get unread notification count")
async def get_unread_count(
    organization_id: UUID = Query(...),
    channel: str | None = Query(None),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    count = await service.get_unread_count(user_id, organization_id, channel)
    return {"unread_count": count}


@router.patch("/notifications/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notification_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    await service.mark_read(notification_id)
    return {"status": "ok"}


@router.post("/notifications/read-all", summary="Mark all notifications as read")
async def mark_all_notifications_read(
    organization_id: UUID,
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    count = await service.mark_all_read(user_id, organization_id)
    return {"marked_read": count}


@router.patch("/notifications/{notification_id}/archive", summary="Archive notification")
async def archive_notification(
    notification_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    await service.archive_notification(notification_id)
    return {"status": "ok"}


@router.get("/notifications/search", summary="Search notifications")
async def search_notifications(
    organization_id: UUID = Query(...),
    q: str = Query(...),
    limit: int = Query(50),
    offset: int = Query(0),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.search_notifications(
        user_id=user_id, organization_id=organization_id,
        q=q, limit=limit, offset=offset,
    )


@router.post("/notifications/send", status_code=201, summary="Send notification")
async def send_notification(
    request: SendNotificationRequest,
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    try:
        notification = await service.send(
            organization_id=request.organization_id,
            user_id=request.user_id, type=request.type,
            title=request.title, body=request.body,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            channel=request.channel,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(notification.id), "status": "sent"}


@router.post("/notifications/send-from-template", status_code=201, summary="Send notification from template")
async def send_from_template(
    request: SendFromTemplateRequest,
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    try:
        notification = await service.send_from_template(
            organization_id=request.organization_id,
            user_id=request.user_id, template_id=request.template_id,
            variables=request.variables,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
        )
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(notification.id), "status": "sent"}


# ── Templates ────────────────────────────────────────────────────────────────

@router.post("/notification-templates", status_code=status.HTTP_201_CREATED, summary="Create notification template")
async def create_template(
    request: CreateTemplateRequest,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        t = await service.create_template(
            org_id=organization_id, name=request.name,
            type=request.type, channel=request.channel,
            title_template=request.title_template,
            body_template=request.body_template,
            variables=request.variables,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(t.id), "name": t.name, "type": t.type, "channel": t.channel}


@router.get("/notification-templates", summary="List notification templates")
async def list_templates(
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_templates(org_id=organization_id)


@router.get("/notification-templates/{template_id}", summary="Get notification template")
async def get_template(
    template_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        t = await service.get_template(template_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found") from None
    return {
        "id": str(t.id), "name": t.name, "type": t.type,
        "channel": t.channel, "title_template": t.title_template,
        "body_template": t.body_template, "variables": t.variables,
        "created_at": t.created_at.isoformat(),
    }


@router.delete("/notification-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete notification template")
async def delete_template(
    template_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_template(template_id)


# ── Preferences ──────────────────────────────────────────────────────────────

@router.put("/notification-preferences", summary="Set notification preference")
async def set_preference(
    request: SetPreferenceRequest,
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    pref = await service.set_preference(
        user_id=user_id, notification_type=request.notification_type,
        channel=request.channel, enabled=request.enabled,
    )
    return {
        "id": str(pref.id), "notification_type": pref.notification_type,
        "channel": pref.channel, "enabled": pref.enabled,
    }


@router.get("/notification-preferences", summary="Get notification preferences")
async def get_preferences(
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
) -> list[dict]:
    return await service.get_preferences(user_id)


# ── Announcements ────────────────────────────────────────────────────────────

@router.post("/announcements", status_code=status.HTTP_201_CREATED, summary="Create announcement")
async def create_announcement(
    request: CreateAnnouncementRequest,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    try:
        a = await service.create_announcement(
            org_id=organization_id, title=request.title,
            body=request.body, severity=request.severity,
            target_role=request.target_role, created_by=user_id,
            expires_at=request.expires_at,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from None
    return {"id": str(a.id), "title": a.title, "severity": a.severity}


@router.get("/announcements", summary="List announcements")
async def list_announcements(
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    return await service.list_announcements(org_id=organization_id)


@router.post("/announcements/{announcement_id}/dismiss", summary="Dismiss announcement")
async def dismiss_announcement(
    announcement_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(organization_id, "viewer", user_id, db)
    await service.dismiss_announcement(announcement_id, user_id)
    return {"status": "ok"}


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete announcement")
async def delete_announcement(
    announcement_id: UUID,
    organization_id: UUID = Query(...),
    service: NotificationHubService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    await service.delete_announcement(announcement_id)
