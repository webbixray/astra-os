"""Social Media Intelligence Entities — Comments, Auto-Reply, Chat.

E6/M7: Social media comment monitoring, sentiment analysis, and AI-powered auto-reply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now

# --- Enums ---


class SocialPlatform(str, Enum):
    META = "meta"  # Facebook/Instagram

    class SocialPlatform(str, Enum):
        META = "meta"  # Facebook/Instagram
        LINKEDIN = "linkedin"
        TWITTER = "twitter"  # X
        TIKTOK = "tiktok"
        YOUTUBE = "youtube"
        GOOGLE = "google"  # Google Ads/Reviews


class CommentType(str, Enum):
    ORGANIC = "organic"  # Regular post comment
    AD_COMMENT = "ad_comment"  # Paid ad comment
    DM = "dm"  # Direct message
    MENTION = "mention"  # @mention
    REPLY = "reply"  # Reply to our comment
    REVIEW = "review"  # Google/Facebook review


class CommentSentiment(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class CommentIntent(str, Enum):
    QUESTION = "question"  # Asking about product/service
    COMPLAINT = "complaint"  # Expressing dissatisfaction
    PRAISE = "praise"  # Positive feedback
    SPAM = "spam"  # Irrelevant/promotional
    LEAD = "lead"  # Interested in purchasing
    SUPPORT = "support"  # Technical support request
    PRICING = "pricing"  # Asking about price
    FEATURE_REQUEST = "feature_request"
    COMPETITOR_MENTION = "competitor_mention"
    INAPPROPRIATE = "inappropriate"  # Toxic/harmful content
    OTHER = "other"


class ReplyStatus(str, Enum):
    PENDING = "pending"  # AI generated, awaiting review
    APPROVED = "approved"  # Ready to send
    SENT = "sent"  # Successfully posted
    REJECTED = "rejected"  # Human rejected
    FAILED = "failed"  # API error
    SKIPPED = "skipped"  # Auto-skipped (low confidence)


class ModerationAction(str, Enum):
    NONE = "none"
    HIDE = "hide"  # Hide comment
    DELETE = "delete"  # Delete comment
    BLOCK_USER = "block_user"  # Block user
    REPORT = "report"  # Report to platform
    FLAG_REVIEW = "flag_review"  # Flag for human review


# --- Entities ---


@dataclass
class SocialComment:
    """A comment or message from social media platforms."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    campaign_id: UUID | None = None
    ad_id: UUID | None = None

    # Platform info
    platform: SocialPlatform = SocialPlatform.META
    platform_comment_id: str = ""
    platform_user_id: str = ""
    platform_username: str = ""
    platform_user_avatar: str | None = None

    # Content
    type: CommentType = CommentType.ORGANIC
    text: str = ""
    original_text: str | None = None  # For translated comments

    # Analysis
    sentiment: CommentSentiment = CommentSentiment.NEUTRAL
    sentiment_score: float = 0.0  # -1.0 to 1.0
    intent: CommentIntent = CommentIntent.OTHER
    intent_confidence: float = 0.0
    language: str = "en"
    is_translated: bool = False

    # Entities extracted
    mentioned_products: list[str] = field(default_factory=list)
    mentioned_competitors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # Engagement
    like_count: int = 0
    reply_count: int = 0
    share_count: int = 0

    # Threading
    parent_comment_id: UUID | None = None
    thread_id: str | None = None
    thread_depth: int = 0

    # Moderation
    moderation_action: ModerationAction = ModerationAction.NONE
    moderation_reason: str = ""
    flagged_for_review: bool = False
    spam_score: float = 0.0
    toxicity_score: float = 0.0

    # Timestamps
    posted_at: datetime = field(default_factory=now)
    fetched_at: datetime = field(default_factory=now)
    analyzed_at: datetime | None = None

    # Metadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "ad_id": str(self.ad_id) if self.ad_id else None,
            "platform": self.platform.value,
            "platform_comment_id": self.platform_comment_id,
            "platform_user_id": self.platform_user_id,
            "platform_username": self.platform_username,
            "platform_user_avatar": self.platform_user_avatar,
            "type": self.type.value,
            "text": self.text,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "intent": self.intent.value,
            "intent_confidence": self.intent_confidence,
            "language": self.language,
            "mentioned_products": self.mentioned_products,
            "mentioned_competitors": self.mentioned_competitors,
            "keywords": self.keywords,
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "share_count": self.share_count,
            "parent_comment_id": str(self.parent_comment_id) if self.parent_comment_id else None,
            "thread_id": self.thread_id,
            "thread_depth": self.thread_depth,
            "moderation_action": self.moderation_action.value,
            "moderation_reason": self.moderation_reason,
            "flagged_for_review": self.flagged_for_review,
            "spam_score": self.spam_score,
            "toxicity_score": self.toxicity_score,
            "posted_at": self.posted_at.isoformat() if self.posted_at else "",
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else "",
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }

    def needs_human_review(self) -> bool:
        """Determine if comment needs human moderation."""
        return (
            self.flagged_for_review
            or self.toxicity_score > 0.8
            or self.spam_score > 0.9
            or self.sentiment == CommentSentiment.VERY_NEGATIVE
            or self.intent == CommentIntent.INAPPROPRIATE
        )


@dataclass
class AutoReply:
    """AI-generated reply to a social comment."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    comment_id: UUID = field(default_factory=uuid4)
    campaign_id: UUID | None = None

    # Generated content
    suggested_text: str = ""
    alternative_texts: list[str] = field(default_factory=list)

    # Generation metadata
    model_used: str = ""  # e.g., "gpt-4o", "claude-3.5-sonnet"
    prompt_version: str = ""
    generation_params: dict[str, Any] = field(default_factory=dict)

    # Confidence & quality
    confidence_score: float = 0.0  # 0.0 to 1.0
    relevance_score: float = 0.0
    brand_voice_score: float = 0.0
    safety_score: float = 0.0

    # Status & workflow
    status: ReplyStatus = ReplyStatus.PENDING
    generated_at: datetime = field(default_factory=now)
    reviewed_at: datetime | None = None
    reviewed_by: UUID | None = None
    review_notes: str = ""

    # Approval & sending
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    sent_at: datetime | None = None
    sent_by: UUID | None = None
    platform_reply_id: str | None = None
    error_message: str = ""

    # A/B testing
    variant: str = "A"
    ab_test_group: str | None = None

    # Context used for generation
    context_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "comment_id": str(self.comment_id),
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "suggested_text": self.suggested_text,
            "alternative_texts": self.alternative_texts,
            "model_used": self.model_used,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "brand_voice_score": self.brand_voice_score,
            "safety_score": self.safety_score,
            "status": self.status.value,
            "generated_at": self.generated_at.isoformat() if self.generated_at else "",
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "platform_reply_id": self.platform_reply_id,
            "error_message": self.error_message,
            "variant": self.variant,
        }

    def can_auto_send(self, threshold: float = 0.85) -> bool:
        """Check if reply can be sent automatically without human review."""
        return (
            self.status == ReplyStatus.PENDING
            and self.confidence_score >= threshold
            and self.relevance_score >= threshold
            and self.brand_voice_score >= threshold
            and self.safety_score >= 0.95
        )


@dataclass
class SocialInbox:
    """Aggregated inbox for social media comments across platforms."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Filters
    platforms: list[SocialPlatform] = field(default_factory=list)
    campaigns: list[UUID] = field(default_factory=list)
    sentiment_filter: list[CommentSentiment] = field(default_factory=list)
    intent_filter: list[CommentIntent] = field(default_factory=list)
    status_filter: list[ReplyStatus] = field(default_factory=list)
    assigned_to: UUID | None = None

    # Pagination
    page: int = 1
    page_size: int = 50

    # Sorting
    sort_by: str = "posted_at"  # posted_at, sentiment_score, priority
    sort_order: str = "desc"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "platforms": [p.value for p in self.platforms],
            "campaigns": [str(c) for c in self.campaigns],
            "sentiment_filter": [s.value for s in self.sentiment_filter],
            "intent_filter": [i.value for i in self.intent_filter],
            "status_filter": [s.value for s in self.status_filter],
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "page": self.page,
            "page_size": self.page_size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }


@dataclass
class ReplyTemplate:
    """Reusable reply templates for common scenarios."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    name: str = ""
    description: str = ""

    # Trigger conditions
    intent_triggers: list[CommentIntent] = field(default_factory=list)
    sentiment_triggers: list[CommentSentiment] = field(default_factory=list)
    keyword_triggers: list[str] = field(default_factory=list)
    platform_triggers: list[SocialPlatform] = field(default_factory=list)

    # Template content
    template_text: str = ""
    variables: list[str] = field(default_factory=list)  # e.g., ["user_name", "product_name"]

    # AI enhancement
    use_ai_enhancement: bool = True
    ai_instructions: str = ""

    # Settings
    is_active: bool = True
    priority: int = 0
    auto_approve_threshold: float = 0.9

    # Stats
    usage_count: int = 0
    success_rate: float = 0.0

    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "intent_triggers": [i.value for i in self.intent_triggers],
            "sentiment_triggers": [s.value for s in self.sentiment_triggers],
            "keyword_triggers": self.keyword_triggers,
            "platform_triggers": [p.value for p in self.platform_triggers],
            "template_text": self.template_text,
            "variables": self.variables,
            "use_ai_enhancement": self.use_ai_enhancement,
            "ai_instructions": self.ai_instructions,
            "is_active": self.is_active,
            "priority": self.priority,
            "auto_approve_threshold": self.auto_approve_threshold,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
        }


# --- Analytics Entities ---


@dataclass
class CommentAnalytics:
    """Aggregated analytics for social comments."""

    organization_id: UUID
    period_start: datetime
    period_end: datetime

    # Volume
    total_comments: int = 0
    comments_by_platform: dict[str, int] = field(default_factory=dict)
    comments_by_type: dict[str, int] = field(default_factory=dict)
    comments_by_sentiment: dict[str, int] = field(default_factory=dict)
    comments_by_intent: dict[str, int] = field(default_factory=dict)

    # Engagement
    total_likes: int = 0
    total_replies: int = 0
    total_shares: int = 0
    avg_engagement_rate: float = 0.0

    # Response metrics
    total_replies_sent: int = 0
    auto_replies_sent: int = 0
    manual_replies_sent: int = 0
    avg_response_time_hours: float = 0.0
    response_rate: float = 0.0  # % of comments replied to

    # Quality
    avg_sentiment_score: float = 0.0
    positive_sentiment_pct: float = 0.0
    negative_sentiment_pct: float = 0.0
    spam_detected: int = 0
    toxicity_flagged: int = 0

    # Auto-reply performance
    auto_reply_generated: int = 0
    auto_reply_sent: int = 0
    auto_reply_approval_rate: float = 0.0
    auto_reply_confidence_avg: float = 0.0

    # Team performance
    replies_by_user: dict[str, int] = field(default_factory=dict)
    avg_response_time_by_user: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_comments": self.total_comments,
            "comments_by_platform": self.comments_by_platform,
            "comments_by_type": self.comments_by_type,
            "comments_by_sentiment": self.comments_by_sentiment,
            "comments_by_intent": self.comments_by_intent,
            "total_likes": self.total_likes,
            "total_replies": self.total_replies,
            "total_shares": self.total_shares,
            "avg_engagement_rate": self.avg_engagement_rate,
            "total_replies_sent": self.total_replies_sent,
            "auto_replies_sent": self.auto_replies_sent,
            "manual_replies_sent": self.manual_replies_sent,
            "avg_response_time_hours": self.avg_response_time_hours,
            "response_rate": self.response_rate,
            "avg_sentiment_score": self.avg_sentiment_score,
            "positive_sentiment_pct": self.positive_sentiment_pct,
            "negative_sentiment_pct": self.negative_sentiment_pct,
            "spam_detected": self.spam_detected,
            "toxicity_flagged": self.toxicity_flagged,
            "auto_reply_generated": self.auto_reply_generated,
            "auto_reply_sent": self.auto_reply_sent,
            "auto_reply_approval_rate": self.auto_reply_approval_rate,
            "auto_reply_confidence_avg": self.auto_reply_confidence_avg,
            "replies_by_user": self.replies_by_user,
        }
