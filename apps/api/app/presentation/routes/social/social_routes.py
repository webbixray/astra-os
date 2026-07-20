"""Social Intelligence API Routes — E6.1/E6.2 Beta Launch.

Endpoints for social media comments, AI auto-reply, inbox management, and analytics.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.social_intelligence import (
    CommentIntent,
    CommentSentiment,
    CommentType,
    ModerationAction,
    ReplyStatus,
    ReplyTemplate,
    SocialPlatform,
)
from app.domain.services.social_intelligence import (
    reply_template_manager,
    social_inbox_manager,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter(prefix="/social", tags=["social-intelligence"])


# --- Request/Response Models ---


class SocialCommentResponse(BaseModel):
    id: str
    organization_id: str
    campaign_id: str | None
    ad_id: str | None
    platform: str
    platform_comment_id: str
    platform_user_id: str
    platform_username: str
    platform_user_avatar: str | None
    type: str
    text: str
    sentiment: str
    sentiment_score: float
    intent: str
    intent_confidence: float
    language: str
    mentioned_products: list[str]
    mentioned_competitors: list[str]
    keywords: list[str]
    like_count: int
    reply_count: int
    share_count: int
    parent_comment_id: str | None
    thread_id: str | None
    thread_depth: int
    moderation_action: str
    moderation_reason: str
    flagged_for_review: bool
    spam_score: float
    toxicity_score: float
    posted_at: str
    fetched_at: str
    analyzed_at: str | None


class GenerateReplyRequest(BaseModel):
    template_id: UUID | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class AutoReplyResponse(BaseModel):
    id: str
    organization_id: str
    comment_id: str
    campaign_id: str | None
    suggested_text: str
    alternative_texts: list[str]
    model_used: str
    confidence_score: float
    relevance_score: float
    brand_voice_score: float
    safety_score: float
    status: str
    generated_at: str
    reviewed_at: str | None
    reviewed_by: str | None
    approved_at: str | None
    approved_by: str | None
    sent_at: str | None
    sent_by: str | None
    platform_reply_id: str | None
    error_message: str
    variant: str


class ApproveReplyRequest(BaseModel):
    approved_by: UUID
    edited_text: str | None = None


class SocialInboxRequest(BaseModel):
    platforms: list[str] = Field(default_factory=list)
    campaigns: list[str] = Field(default_factory=list)
    sentiment_filter: list[str] = Field(default_factory=list)
    intent_filter: list[str] = Field(default_factory=list)
    status_filter: list[str] = Field(default_factory=list)
    assigned_to: str | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "posted_at"
    sort_order: str = "desc"


class InboxStatsResponse(BaseModel):
    total_pending: int
    total_assigned: int
    avg_response_time_hours: float
    by_platform: dict[str, int]
    by_sentiment: dict[str, int]
    by_intent: dict[str, int]
    sla_breach_count: int


class ReplyTemplateRequest(BaseModel):
    name: str
    description: str
    intent_triggers: list[str]
    sentiment_triggers: list[str]
    keyword_triggers: list[str]
    platform_triggers: list[str]
    template_text: str
    variables: list[str]
    use_ai_enhancement: bool = True
    ai_instructions: str = ""
    is_active: bool = True
    priority: int = 0
    auto_approve_threshold: float = 0.9


class CommentAnalyticsResponse(BaseModel):
    organization_id: str
    period_start: str
    period_end: str
    total_comments: int
    comments_by_platform: dict[str, int]
    comments_by_type: dict[str, int]
    comments_by_sentiment: dict[str, int]
    comments_by_intent: dict[str, int]
    total_likes: int
    total_replies: int
    total_shares: int
    avg_engagement_rate: float
    total_replies_sent: int
    auto_replies_sent: int
    manual_replies_sent: int
    avg_response_time_hours: float
    response_rate: float
    avg_sentiment_score: float
    positive_sentiment_pct: float
    negative_sentiment_pct: float
    spam_detected: int
    toxicity_flagged: int
    auto_reply_generated: int
    auto_reply_sent: int
    auto_reply_approval_rate: float
    auto_reply_confidence_avg: float
    replies_by_user: dict[str, int]


# --- Dependencies ---


async def _require_org_access(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "viewer", user_id, db)
    return organization_id


async def _require_org_admin(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "admin", user_id, db)
    return organization_id


# --- Comment Routes ---


@router.get(
    "/organizations/{organization_id}/comments",
    response_model=list[SocialCommentResponse],
    summary="List comments with filters",
)
async def list_comments(
    organization_id: UUID,
    platform: SocialPlatform | None = Query(None),
    campaign_id: UUID | None = Query(None),
    ad_id: UUID | None = Query(None),
    sentiment: CommentSentiment | None = Query(None),
    intent: CommentIntent | None = Query(None),
    type: CommentType | None = Query(None),
    flagged_only: bool = Query(False),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List social comments with filtering."""
    # In production: query database with filters
    return []


@router.get(
    "/organizations/{organization_id}/comments/{comment_id}",
    response_model=SocialCommentResponse,
    summary="Get a specific comment",
)
async def get_comment(
    organization_id: UUID,
    comment_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific comment by ID."""
    # In production: query database
    raise HTTPException(status_code=404, detail="Comment not found")


@router.patch(
    "/organizations/{organization_id}/comments/{comment_id}/moderate",
    summary="Apply moderation action to a comment",
)
async def moderate_comment(
    organization_id: UUID,
    comment_id: UUID,
    action: ModerationAction,
    reason: str = "",
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Apply moderation action (hide, delete, block, report, flag)."""
    # In production: call platform API
    return {"message": f"Moderation action '{action.value}' applied", "comment_id": str(comment_id)}


# --- Auto-Reply Routes ---


@router.post(
    "/organizations/{organization_id}/comments/{comment_id}/reply/generate",
    response_model=AutoReplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI reply for a comment",
)
async def generate_reply(
    organization_id: UUID,
    comment_id: UUID,
    request: GenerateReplyRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate an AI-powered reply for a comment."""
    # In production: fetch comment, generate reply, save
    raise HTTPException(status_code=404, detail="Comment not found")


@router.get(
    "/organizations/{organization_id}/replies",
    response_model=list[AutoReplyResponse],
    summary="List auto-replies",
)
async def list_replies(
    organization_id: UUID,
    status: ReplyStatus | None = Query(None),
    comment_id: UUID | None = Query(None),
    campaign_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List auto-replies with filters."""
    return []


@router.get(
    "/organizations/{organization_id}/replies/{reply_id}",
    response_model=AutoReplyResponse,
    summary="Get a specific reply",
)
async def get_reply(
    organization_id: UUID,
    reply_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific auto-reply."""
    raise HTTPException(status_code=404, detail="Reply not found")


@router.patch(
    "/organizations/{organization_id}/replies/{reply_id}/approve",
    response_model=AutoReplyResponse,
    summary="Approve an auto-reply",
)
async def approve_reply(
    organization_id: UUID,
    reply_id: UUID,
    request: ApproveReplyRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Approve an auto-reply for sending."""
    raise HTTPException(status_code=404, detail="Reply not found")


@router.post(
    "/organizations/{organization_id}/replies/{reply_id}/send",
    response_model=AutoReplyResponse,
    summary="Send an approved reply",
)
async def send_reply(
    organization_id: UUID,
    reply_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send an approved reply to the platform."""
    raise HTTPException(status_code=404, detail="Reply not found")


@router.post(
    "/organizations/{organization_id}/replies/{reply_id}/reject",
    response_model=AutoReplyResponse,
    summary="Reject an auto-reply",
)
async def reject_reply(
    organization_id: UUID,
    reply_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reject an auto-reply."""
    raise HTTPException(status_code=404, detail="Reply not found")


# --- Inbox Routes ---


@router.post(
    "/organizations/{organization_id}/inbox",
    response_model=list[SocialCommentResponse],
    summary="Get filtered inbox view",
)
async def get_inbox(
    organization_id: UUID,
    request: SocialInboxRequest,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get filtered inbox view of comments."""
    return []


@router.get(
    "/organizations/{organization_id}/inbox/stats",
    response_model=InboxStatsResponse,
    summary="Get inbox statistics",
)
async def get_inbox_stats(
    organization_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get inbox statistics."""
    return await social_inbox_manager.get_inbox_stats(organization_id)


@router.post(
    "/organizations/{organization_id}/comments/{comment_id}/assign",
    summary="Assign comment to team member",
)
async def assign_comment(
    organization_id: UUID,
    comment_id: UUID,
    assignee_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Assign a comment to a team member."""
    await require_org_role(organization_id, "admin", assignee_id, db)
    return {
        "message": "Comment assigned",
        "comment_id": str(comment_id),
        "assignee_id": str(assignee_id),
    }


# --- Reply Template Routes ---


@router.post(
    "/organizations/{organization_id}/reply-templates",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reply template",
)
async def create_reply_template(
    organization_id: UUID,
    request: ReplyTemplateRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new reply template."""
    template = ReplyTemplate(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        intent_triggers=[CommentIntent(t) for t in request.intent_triggers],
        sentiment_triggers=[CommentSentiment(t) for t in request.sentiment_triggers],
        keyword_triggers=request.keyword_triggers,
        platform_triggers=[SocialPlatform(t) for t in request.platform_triggers],
        template_text=request.template_text,
        variables=request.variables,
        use_ai_enhancement=request.use_ai_enhancement,
        ai_instructions=request.ai_instructions,
        is_active=request.is_active,
        priority=request.priority,
        auto_approve_threshold=request.auto_approve_threshold,
    )
    created = reply_template_manager.create_template(template)
    return created.to_dict()


@router.get(
    "/organizations/{organization_id}/reply-templates",
    response_model=list[dict],
    summary="List reply templates",
)
async def list_reply_templates(
    organization_id: UUID,
    active_only: bool = Query(True),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List reply templates for an organization."""
    return []


@router.get(
    "/organizations/{organization_id}/reply-templates/{template_id}",
    response_model=dict,
    summary="Get a reply template",
)
async def get_reply_template(
    organization_id: UUID,
    template_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific reply template."""
    template = reply_template_manager.get_template(template_id)
    if not template or template.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@router.patch(
    "/organizations/{organization_id}/reply-templates/{template_id}",
    response_model=dict,
    summary="Update a reply template",
)
async def update_reply_template(
    organization_id: UUID,
    template_id: UUID,
    request: ReplyTemplateRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a reply template."""
    raise HTTPException(status_code=404, detail="Template not found")


@router.delete(
    "/organizations/{organization_id}/reply-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reply template",
)
async def delete_reply_template(
    organization_id: UUID,
    template_id: UUID,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a reply template."""


@router.post(
    "/organizations/{organization_id}/reply-templates/{template_id}/match",
    response_model=list[dict],
    summary="Find matching templates for a comment",
)
async def match_templates(
    organization_id: UUID,
    template_id: UUID,
    comment_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Find templates matching a comment."""
    return []


# --- Analytics Routes ---


@router.get(
    "/organizations/{organization_id}/analytics/comments",
    response_model=CommentAnalyticsResponse,
    summary="Get comment analytics",
)
async def get_comment_analytics(
    organization_id: UUID,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get comment analytics for a period."""
    return {
        "organization_id": str(organization_id),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "total_comments": 0,
        "comments_by_platform": {},
        "comments_by_type": {},
        "comments_by_sentiment": {},
        "comments_by_intent": {},
        "total_likes": 0,
        "total_replies": 0,
        "total_shares": 0,
        "avg_engagement_rate": 0.0,
        "total_replies_sent": 0,
        "auto_replies_sent": 0,
        "manual_replies_sent": 0,
        "avg_response_time_hours": 0.0,
        "response_rate": 0.0,
        "avg_sentiment_score": 0.0,
        "positive_sentiment_pct": 0.0,
        "negative_sentiment_pct": 0.0,
        "spam_detected": 0,
        "toxicity_flagged": 0,
        "auto_reply_generated": 0,
        "auto_reply_sent": 0,
        "auto_reply_approval_rate": 0.0,
        "auto_reply_confidence_avg": 0.0,
        "replies_by_user": {},
    }


@router.get(
    "/organizations/{organization_id}/analytics/sentiment-trends",
    summary="Get sentiment trends over time",
)
async def get_sentiment_trends(
    organization_id: UUID,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    granularity: str = Query("day", pattern="^(hour|day|week|month)$"),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get sentiment trends over time."""
    return {"trends": []}


@router.get(
    "/organizations/{organization_id}/analytics/top-comments",
    summary="Get top engaging comments",
)
async def get_top_comments(
    organization_id: UUID,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    metric: str = Query("engagement", pattern="^(likes|replies|shares|engagement)$"),
    limit: int = Query(10, le=50),
    org_id: UUID = Depends(_require_org_access),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get top comments by engagement metric."""
    return []


# --- Batch Operations ---


@router.post(
    "/organizations/{organization_id}/comments/batch-moderate",
    summary="Batch moderate comments",
)
async def batch_moderate(
    organization_id: UUID,
    comment_ids: list[UUID],
    action: str,
    reason: str = "",
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Apply moderation action to multiple comments."""
    return {"processed": len(comment_ids), "action": action}


@router.post(
    "/organizations/{organization_id}/replies/batch-approve",
    summary="Batch approve auto-replies",
)
async def batch_approve_replies(
    organization_id: UUID,
    reply_ids: list[UUID],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Approve multiple auto-replies at once."""
    return {"approved": len(reply_ids)}


@router.post(
    "/organizations/{organization_id}/replies/batch-send",
    summary="Batch send approved replies",
)
async def batch_send_replies(
    organization_id: UUID,
    reply_ids: list[UUID],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send multiple approved replies."""
    return {"sent": 0, "failed": 0, "details": []}


# --- Webhook Routes ---


@router.post(
    "/webhooks/{platform}/comments",
    status_code=status.HTTP_200_OK,
    summary="Receive comment webhook from platform",
)
async def receive_comment_webhook(
    platform: SocialPlatform,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Receive incoming comment webhook from social platforms."""
    return {"received": True, "platform": platform.value}
