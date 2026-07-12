"""Social Intelligence Services — E6.1/E6.2 Beta Launch.

AI-powered comment analysis, auto-reply generation, and social inbox management.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.entities.social_intelligence import (
    AutoReply,
    CommentAnalytics,
    CommentIntent,
    CommentSentiment,
    CommentType,
    ModerationAction,
    ReplyStatus,
    ReplyTemplate,
    SocialComment,
    SocialInbox,
    SocialPlatform,
)

logger = logging.getLogger(__name__)


# --- Comment Analyzer ---

class CommentAnalyzer:
    """Analyzes social media comments for sentiment, intent, entities, and moderation."""

    # Intent detection patterns
    INTENT_PATTERNS: dict[CommentIntent, list[str]] = {
        CommentIntent.QUESTION: [
            r"\b(how|what|when|where|why|who|which)\b",
            r"\?",
            r"\b(can you|could you|would you|will you)\b",
            r"\b(tell me|explain|clarify)\b",
        ],
        CommentIntent.COMPLAINT: [
            r"\b(bad|terrible|awful|horrible|worst|disappointed|frustrated|angry)\b",
            r"\b(complaint|issue|problem|broken|not working|failed|error)\b",
            r"\b(refund|money back|cancel|useless|waste)\b",
        ],
        CommentIntent.PRAISE: [
            r"\b(love|amazing|awesome|great|excellent|fantastic|perfect|best)\b",
            r"\b(thank you|thanks|appreciate|grateful|impressed)\b",
            r"\b(keep it up|well done|good job|brilliant)\b",
        ],
        CommentIntent.SPAM: [
            r"\b(buy now|click here|visit my|check out my|follow me|dm me)\b",
            r"\b(make money|earn \$\d+|work from home|investment opportunity)\b",
            r"(https?://\S+){2,}",  # Multiple URLs
            r"[@#]\w{20,}",  # Excessive mentions/hashtags
        ],
        CommentIntent.LEAD: [
            r"\b(interested|want to buy|looking for|need a|searching for)\b",
            r"\b(pricing|price|cost|quote|demo|trial|sign up)\b",
            r"\b(contact me|call me|email me|dm for)\b",
        ],
        CommentIntent.SUPPORT: [
            r"\b(help|support|assist|troubleshoot|fix|resolve)\b",
            r"\b(how to|tutorial|guide|documentation|manual)\b",
            r"\b(bug|error|crash|not loading|not working|issue)\b",
        ],
        CommentIntent.PRICING: [
            r"\b(how much|what.*cost|price|pricing|plan|cost)\b",
            r"\$\d+",
            r"\b(free|trial|discount|coupon|promo)\b",
        ],
        CommentIntent.FEATURE_REQUEST: [
            r"\b(feature|functionality|add|implement|suggestion|request)\b",
            r"\b(wish|would be nice|would love|it would be great)\b",
        ],
        CommentIntent.COMPETITOR_MENTION: [
            r"\b(competitor|alternative|better than|switch from|instead of)\b",
            # Specific competitor names would be added per organization
        ],
        CommentIntent.INAPPROPRIATE: [
            r"\b(hate|stupid|idiot|moron|garbage|trash|scam|fraud)\b",
            # More sophisticated toxicity detection would use ML model
        ],
    }

    # Sentiment keywords
    POSITIVE_WORDS = {
        "love", "amazing", "awesome", "great", "excellent", "fantastic", "perfect",
        "best", "wonderful", "brilliant", "outstanding", "superb", "impressive",
        "happy", "satisfied", "pleased", "delighted", "thrilled", "excited",
        "thanks", "thank you", "appreciate", "grateful", "recommend", "favorite"
    }

    NEGATIVE_WORDS = {
        "hate", "terrible", "awful", "horrible", "worst", "bad", "poor", "disappointing",
        "frustrated", "angry", "annoyed", "upset", "unhappy", "dissatisfied",
        "useless", "waste", "broken", "failed", "error", "problem", "issue",
        "complaint", "refund", "cancel", "regret", "mistake", "avoid"
    }

    TOXIC_WORDS = {
        "hate", "stupid", "idiot", "moron", "garbage", "trash", "scam", "fraud",
        "die", "kill", "die", "worthless", "pathetic", "disgusting", "vile"
    }

    SPAM_INDICATORS = [
        r"(https?://\S+){2,}",  # Multiple URLs
        r"[@#]\w{20,}",  # Excessive mentions/hashtags
        r"\b(buy now|click here|visit my|check out my|follow me|dm me|link in bio)\b",
        r"\b(make money|earn \$\d+|work from home|investment opportunity|get rich)\b",
        r"(.)\1{10,}",  # Character repetition
        r"[A-Z]{20,}",  # Excessive caps
    ]

    def __init__(self):
        self._compiled_patterns: dict[CommentIntent, list[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for intent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._spam_patterns = [re.compile(p, re.IGNORECASE) for p in self.SPAM_INDICATORS]

    def analyze(self, comment: SocialComment) -> SocialComment:
        """Run full analysis on a comment."""
        text = comment.text.lower()

        # Sentiment analysis
        comment.sentiment, comment.sentiment_score = self._analyze_sentiment(text)

        # Intent detection
        comment.intent, comment.intent_confidence = self._detect_intent(text)

        # Entity extraction
        comment.mentioned_products = self._extract_products(text)
        comment.mentioned_competitors = self._extract_competitors(text)
        comment.keywords = self._extract_keywords(text)

        # Spam & toxicity
        comment.spam_score = self._calculate_spam_score(comment.text)
        comment.toxicity_score = self._calculate_toxicity_score(text)

        # Moderation flags
        if comment.toxicity_score > 0.8:
            comment.flagged_for_review = True
            comment.moderation_action = ModerationAction.FLAG_REVIEW

        if comment.spam_score > 0.9:
            comment.moderation_action = ModerationAction.HIDE

        # Language detection (simplified)
        comment.language = self._detect_language(comment.text)

        comment.analyzed_at = now()
        return comment

    def _analyze_sentiment(self, text: str) -> tuple[CommentSentiment, float]:
        words = set(re.findall(r"\b\w+\b", text.lower()))
        pos_count = len(words & self.POSITIVE_WORDS)
        neg_count = len(words & self.NEGATIVE_WORDS)

        if pos_count == 0 and neg_count == 0:
            return CommentSentiment.NEUTRAL, 0.0

        total = pos_count + neg_count
        score = (pos_count - neg_count) / total

        if score >= 0.5:
            return CommentSentiment.VERY_POSITIVE, score
        elif score > 0.1:
            return CommentSentiment.POSITIVE, score
        elif score >= -0.1:
            return CommentSentiment.NEUTRAL, score
        elif score > -0.5:
            return CommentSentiment.NEGATIVE, score
        else:
            return CommentSentiment.VERY_NEGATIVE, score

    def _detect_intent(self, text: str) -> tuple[CommentIntent, float]:
        intent_scores: dict[CommentIntent, int] = {}

        for intent, patterns in self._compiled_patterns.items():
            matches = sum(1 for p in patterns if p.search(text))
            if matches > 0:
                intent_scores[intent] = matches

        if not intent_scores:
            return CommentIntent.OTHER, 0.0

        top_intent = max(intent_scores, key=intent_scores.get)
        total = sum(intent_scores.values())
        confidence = intent_scores[top_intent] / total if total > 0 else 0.0

        return top_intent, confidence

    def _extract_products(self, text: str) -> list[str]:
        """Extract product mentions (would use NER in production)."""
        # Simplified - in production would use spaCy NER or custom model
        product_keywords = ["product", "service", "platform", "tool", "app", "software"]
        found = []
        for kw in product_keywords:
            if kw in text.lower():
                # Extract surrounding context
                idx = text.lower().find(kw)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(kw) + 30)
                context = text[start:end].strip()
                found.append(context)
        return found[:5]

    def _extract_competitors(self, text: str) -> list[str]:
        """Extract competitor mentions."""
        # Would be configured per organization
        common_competitors = ["competitor", "alternative", "switch", "instead of"]
        found = []
        for kw in common_competitors:
            if kw in text.lower():
                found.append(kw)
        return found

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract key topics/keywords."""
        # Simple TF-IDF style extraction
        words = re.findall(r"\b[a-z]{4,}\b", text.lower())
        stopwords = {"the", "and", "for", "you", "your", "this", "that", "with", "have", "are", "was", "but", "not", "has", "had"}
        filtered = [w for w in words if w not in stopwords]
        # Return top 10 by frequency
        from collections import Counter
        return [w for w, _ in Counter(filtered).most_common(10)]

    def _calculate_spam_score(self, text: str) -> float:
        score = 0.0
        for pattern in self._spam_patterns:
            if pattern.search(text):
                score += 0.2
        return min(score, 1.0)

    def _calculate_toxicity_score(self, text: str) -> float:
        words = set(re.findall(r"\b\w+\b", text.lower()))
        toxic_count = len(words & self.TOXIC_WORDS)
        total_words = len(words)
        return min(toxic_count / max(total_words, 1) * 5, 1.0)

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        # In production, use fasttext or langdetect
        english_indicators = {"the", "and", "you", "for", "with", "this", "that", "have", "are"}
        words = set(re.findall(r"\b\w+\b", text.lower()))
        english_count = len(words & english_indicators)
        if english_count >= 3:
            return "en"
        return "unknown"


# --- Auto-Reply Generator ---

class AutoReplyGenerator:
    """Generates AI-powered replies to social comments."""

    def __init__(
        self,
        analyzer: CommentAnalyzer | None = None,
        model_router=None,
        brand_voice_service=None,
    ):
        self.analyzer = analyzer or CommentAnalyzer()
        self.model_router = model_router
        self.brand_voice_service = brand_voice_service

    async def generate_reply(
        self,
        comment: SocialComment,
        context: dict[str, Any] | None = None,
        template: ReplyTemplate | None = None,
    ) -> AutoReply:
        """Generate an AI reply for a comment."""

        # Build context for generation
        gen_context = {
            "comment_text": comment.text,
            "comment_sentiment": comment.sentiment.value,
            "comment_intent": comment.intent.value,
            "platform": comment.platform.value,
            "user_name": comment.platform_username,
            **(context or {}),
        }

        # Try template first
        suggested_text = ""
        if template:
            suggested_text = self._apply_template(template, gen_context)

        # AI generation
        if not suggested_text or template.use_ai_enhancement if template else True:
            suggested_text = await self._generate_with_ai(gen_context, template)

        # Generate alternatives
        alternatives = await self._generate_alternatives(gen_context, count=2)

        # Score the reply
        reply = AutoReply(
            organization_id=comment.organization_id,
            comment_id=comment.id,
            campaign_id=comment.campaign_id,
            suggested_text=suggested_text,
            alternative_texts=alternatives,
            model_used="gpt-4o",  # Would come from model router
            context_used=gen_context,
        )

        reply.confidence_score = self._score_confidence(reply, comment)
        reply.relevance_score = self._score_relevance(reply, comment)
        reply.brand_voice_score = self._score_brand_voice(reply)
        reply.safety_score = self._score_safety(reply)

        # Auto-approve if high confidence
        if reply.can_auto_send(0.85):
            reply.status = ReplyStatus.APPROVED
            reply.approved_at = now()
            reply.approved_by = uuid4()  # System user

        return reply

    async def _generate_with_ai(
        self,
        context: dict[str, Any],
        template: ReplyTemplate | None = None,
    ) -> str:
        """Generate reply using LLM."""
        # In production, this would call the model router
        # For now, return template-based response
        sentiment = context.get("comment_sentiment", "neutral")
        intent = context.get("comment_intent", "other")
        user_name = context.get("user_name", "there")

        templates = {
            CommentIntent.QUESTION: f"Hi {user_name}! Thanks for your question. ",
            CommentIntent.COMPLAINT: f"Hi {user_name}, I'm sorry to hear about your experience. ",
            CommentIntent.PRAISE: f"Thank you so much, {user_name}! We're thrilled to hear ",
            CommentIntent.LEAD: f"Hi {user_name}! Thanks for your interest in ",
            CommentIntent.SUPPORT: f"Hi {user_name}, I'd be happy to help with ",
            CommentIntent.PRICING: f"Hi {user_name}! For pricing details, ",
        }

        base = templates.get(CommentIntent(intent), f"Hi {user_name}! Thanks for reaching out. ")

        if sentiment == "positive":
            base += "We appreciate your feedback! "
        elif sentiment == "negative":
            base += "We'd love to make this right. "

        base += "Our team will get back to you shortly. Is there anything specific I can help with today?"

        return base

    async def _generate_alternatives(self, context: dict[str, Any], count: int = 2) -> list[str]:
        """Generate alternative reply variations."""
        alternatives = []
        for i in range(count):
            alt = await self._generate_with_ai(context)
            alternatives.append(alt)
        return alternatives

    def _apply_template(self, template: ReplyTemplate, context: dict[str, Any]) -> str:
        """Fill template variables with context."""
        text = template.template_text
        for var in template.variables:
            value = context.get(var, f"{{{var}}}")
            text = text.replace(f"{{{var}}}", str(value))
        return text

    def _score_confidence(self, reply: AutoReply, comment: SocialComment) -> float:
        """Score overall confidence of the reply."""
        base = 0.7
        if comment.intent_confidence > 0.7:
            base += 0.1
        if comment.sentiment in (CommentSentiment.POSITIVE, CommentSentiment.NEUTRAL):
            base += 0.1
        return min(base, 1.0)

    def _score_relevance(self, reply: AutoReply, comment: SocialComment) -> float:
        """Score how relevant the reply is to the comment."""
        # Would use semantic similarity in production
        return 0.85

    def _score_brand_voice(self, reply: AutoReply) -> float:
        """Score adherence to brand voice."""
        # Would check against brand voice guidelines
        return 0.9

    def _score_safety(self, reply: AutoReply) -> float:
        """Score safety of the reply."""
        toxic_words = {"guarantee", "promise", "definitely", "100%", "refund"}
        text_lower = reply.suggested_text.lower()
        penalty = sum(0.1 for word in toxic_words if word in text_lower)
        return max(0.95 - penalty, 0.5)


# --- Social Inbox Manager ---

class SocialInboxManager:
    """Manages the social media inbox - fetching, filtering, assignment."""

    def __init__(self, analyzer: CommentAnalyzer | None = None):
        self.analyzer = analyzer or CommentAnalyzer()

    async def fetch_comments(
        self,
        organization_id: UUID,
        platforms: list[SocialPlatform] | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[SocialComment]:
        """Fetch comments from connected social platforms."""
        # In production, this would call platform APIs
        # For now, return mock data structure
        return []

    async def process_inbox(
        self,
        inbox: SocialInbox,
        comments: list[SocialComment],
    ) -> list[SocialComment]:
        """Process and filter comments for inbox view."""
        filtered = comments

        if inbox.platforms:
            filtered = [c for c in filtered if c.platform in inbox.platforms]

        if inbox.campaigns:
            filtered = [c for c in filtered if c.campaign_id in inbox.campaigns]

        if inbox.sentiment_filter:
            filtered = [c for c in filtered if c.sentiment in inbox.sentiment_filter]

        if inbox.intent_filter:
            filtered = [c for c in filtered if c.intent in inbox.intent_filter]

        if inbox.status_filter:
            pass

        # Sort
        reverse = inbox.sort_order == "desc"
        if inbox.sort_by == "posted_at":
            filtered.sort(key=lambda c: c.posted_at, reverse=reverse)
        elif inbox.sort_by == "sentiment_score":
            filtered.sort(key=lambda c: c.sentiment_score, reverse=reverse)

        # Paginate
        start = (inbox.page - 1) * inbox.page_size
        end = start + inbox.page_size
        return filtered[start:end]

    async def assign_comment(
        self,
        comment_id: UUID,
        assignee_id: UUID,
        assigned_by: UUID,
    ) -> SocialComment:
        """Assign a comment to a team member."""
        # In production, update in database
        return SocialComment(id=comment_id)

    async def get_inbox_stats(self, organization_id: UUID) -> dict[str, Any]:
        """Get inbox statistics."""
        return {
            "total_pending": 0,
            "total_assigned": 0,
            "avg_response_time_hours": 0.0,
            "by_platform": {},
            "by_sentiment": {},
            "by_intent": {},
            "sla_breach_count": 0,
        }


# --- Reply Template Manager ---

class ReplyTemplateManager:
    """Manages reply templates for common scenarios."""

    def __init__(self):
        self.templates: dict[UUID, ReplyTemplate] = {}

    def create_template(self, template: ReplyTemplate) -> ReplyTemplate:
        self.templates[template.id] = template
        return template

    def get_template(self, template_id: UUID) -> ReplyTemplate | None:
        return self.templates.get(template_id)

    def find_matching_templates(
        self,
        comment: SocialComment,
        organization_id: UUID,
    ) -> list[ReplyTemplate]:
        """Find templates matching a comment."""
        matches = []
        for template in self.templates.values():
            if template.organization_id != organization_id:
                continue
            if not template.is_active:
                continue

            # Check intent triggers
            if template.intent_triggers and comment.intent not in template.intent_triggers:
                continue

            # Check sentiment triggers
            if template.sentiment_triggers and comment.sentiment not in template.sentiment_triggers:
                continue

            # Check keyword triggers
            if template.keyword_triggers:
                text_lower = comment.text.lower()
                if not any(kw.lower() in text_lower for kw in template.keyword_triggers):
                    continue

            # Check platform triggers
            if template.platform_triggers and comment.platform not in template.platform_triggers:
                continue

            matches.append(template)

        # Sort by priority
        matches.sort(key=lambda t: t.priority, reverse=True)
        return matches

    def record_usage(self, template_id: UUID, success: bool) -> None:
        """Record template usage for analytics."""
        if template_id in self.templates:
            template = self.templates[template_id]
            template.usage_count += 1
            # Update success rate (exponential moving average)
            alpha = 0.1
            template.success_rate = (1 - alpha) * template.success_rate + alpha * (1.0 if success else 0.0)


# --- Analytics ---

class CommentAnalyticsEngine:
    """Generates analytics for social comments."""

    async def generate_analytics(
        self,
        organization_id: UUID,
        comments: list[SocialComment],
        replies: list[AutoReply],
        period_start: datetime,
        period_end: datetime,
    ) -> CommentAnalytics:
        analytics = CommentAnalytics(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
        )

        analytics.total_comments = len(comments)

        # By platform
        for c in comments:
            analytics.comments_by_platform[c.platform.value] = analytics.comments_by_platform.get(c.platform.value, 0) + 1

        # By type
        for c in comments:
            analytics.comments_by_type[c.type.value] = analytics.comments_by_type.get(c.type.value, 0) + 1

        # By sentiment
        for c in comments:
            analytics.comments_by_sentiment[c.sentiment.value] = analytics.comments_by_sentiment.get(c.sentiment.value, 0) + 1

        # By intent
        for c in comments:
            analytics.comments_by_intent[c.intent.value] = analytics.comments_by_intent.get(c.intent.value, 0) + 1

        # Engagement
        analytics.total_likes = sum(c.like_count for c in comments)
        analytics.total_replies = sum(c.reply_count for c in comments)
        analytics.total_shares = sum(c.share_count for c in comments)

        if comments:
            analytics.avg_engagement_rate = (analytics.total_likes + analytics.total_replies + analytics.total_shares) / len(comments)

        # Response metrics
        sent_replies = [r for r in replies if r.status == ReplyStatus.SENT]
        analytics.total_replies_sent = len(sent_replies)
        analytics.auto_replies_sent = len([r for r in sent_replies if r.approved_by is None])  # System-approved
        analytics.manual_replies_sent = analytics.total_replies_sent - analytics.auto_replies_sent

        if comments:
            analytics.response_rate = len(sent_replies) / len(comments) * 100

        # Sentiment
        sentiment_scores = [c.sentiment_score for c in comments]
        if sentiment_scores:
            analytics.avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
            pos = sum(1 for s in sentiment_scores if s > 0.1)
            neg = sum(1 for s in sentiment_scores if s < -0.1)
            analytics.positive_sentiment_pct = pos / len(comments) * 100
            analytics.negative_sentiment_pct = neg / len(comments) * 100

        # Moderation
        analytics.spam_detected = sum(1 for c in comments if c.spam_score > 0.5)
        analytics.toxicity_flagged = sum(1 for c in comments if c.toxicity_score > 0.5)

        # Auto-reply
        auto_replies = [r for r in replies if r.status in (ReplyStatus.APPROVED, ReplyStatus.SENT)]
        analytics.auto_reply_generated = len(auto_replies)
        analytics.auto_reply_sent = len([r for r in auto_replies if r.status == ReplyStatus.SENT])
        if auto_replies:
            approved = [r for r in auto_replies if r.status != ReplyStatus.REJECTED]
            analytics.auto_reply_approval_rate = len(approved) / len(auto_replies) * 100
            analytics.auto_reply_confidence_avg = sum(r.confidence_score for r in auto_replies) / len(auto_replies)

        return analytics


# --- Singleton instances ---

comment_analyzer = CommentAnalyzer()
auto_reply_generator = AutoReplyGenerator()
social_inbox_manager = SocialInboxManager()
reply_template_manager = ReplyTemplateManager()
comment_analytics_engine = CommentAnalyticsEngine()