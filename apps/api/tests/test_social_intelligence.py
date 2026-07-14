"""Tests for Social Intelligence — Comments, Auto-Reply, Templates, Analytics."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.entities.social_intelligence import (
    AutoReply,
    CommentAnalytics,
    CommentIntent,
    CommentSentiment,
    CommentType,
    ReplyStatus,
    ReplyTemplate,
    SocialComment,
    SocialInbox,
    SocialPlatform,
)
from app.domain.services.social_intelligence import (
    AutoReplyGenerator,
    CommentAnalyticsEngine,
    CommentAnalyzer,
    ReplyTemplateManager,
    SocialInboxManager,
)

# --- CommentAnalyzer Tests ---

class TestCommentAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return CommentAnalyzer()

    @pytest.fixture
    def sample_comment(self):
        return SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            platform_comment_id="comment_123",
            platform_user_id="user_456",
            platform_username="testuser",
            type=CommentType.AD_COMMENT,
            text="This product is amazing! Love the new features. How much does it cost?",
        )

    def test_analyze_positive_sentiment(self, analyzer, sample_comment):
        analyzed = analyzer.analyze(sample_comment)
        assert analyzed.sentiment in (CommentSentiment.POSITIVE, CommentSentiment.VERY_POSITIVE)
        assert analyzed.sentiment_score > 0

    def test_analyze_negative_sentiment(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="This is terrible! Worst product ever. I want a refund!",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.sentiment in (CommentSentiment.NEGATIVE, CommentSentiment.VERY_NEGATIVE)
        assert analyzed.sentiment_score < 0

    def test_analyze_neutral_sentiment(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="The product works as expected. Nothing special.",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.sentiment == CommentSentiment.NEUTRAL

    def test_detect_question_intent(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="How does this work? Can you explain the pricing?",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.intent == CommentIntent.QUESTION
        assert analyzed.intent_confidence > 0.5

    def test_detect_complaint_intent(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="This is broken! Terrible service, want my money back!",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.intent == CommentIntent.COMPLAINT

    def test_detect_praise_intent(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="Love this product! Amazing work team!",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.intent == CommentIntent.PRAISE

    def test_detect_spam(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="Buy now! Click here! Visit my profile! Make money fast! http://spam.com http://spam2.com",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.intent == CommentIntent.SPAM
        assert analyzed.spam_score > 0.5

    def test_detect_lead_intent(self, analyzer):
        comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="I'm interested in buying this. What's the pricing? Can I get a demo?",
        )
        analyzed = analyzer.analyze(comment)
        assert analyzed.intent == CommentIntent.LEAD

    def test_spam_score_calculation(self, analyzer):
        spam_text = "Buy now! Click here! Check out my link! http://spam.com"
        score = analyzer._calculate_spam_score(spam_text)
        assert score > 0.5

    def test_toxicity_score_calculation(self, analyzer):
        toxic_text = "This is stupid garbage trash scam"
        score = analyzer._calculate_toxicity_score(toxic_text)
        assert score > 0.5

    def test_language_detection(self, analyzer):
        english = "This is a test comment in English"
        assert analyzer._detect_language(english) == "en"

    def test_moderation_flags(self, analyzer):
        toxic_comment = SocialComment(
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="This is garbage trash scam! I hate it!",
        )
        analyzed = analyzer.analyze(toxic_comment)
        assert analyzed.flagged_for_review is True


# --- AutoReplyGenerator Tests ---

class TestAutoReplyGenerator:
    @pytest.fixture
    def generator(self):
        return AutoReplyGenerator()

    @pytest.fixture
    def analyzed_comment(self):
        return SocialComment(
            id=uuid4(),
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            platform_comment_id="c123",
            platform_user_id="u456",
            platform_username="testuser",
            type=CommentType.AD_COMMENT,
            text="How much does this cost?",
            sentiment=CommentSentiment.NEUTRAL,
            sentiment_score=0.0,
            intent=CommentIntent.PRICING,
            intent_confidence=0.9,
        )

    @pytest.mark.asyncio
    async def test_generate_reply_for_pricing(self, generator, analyzed_comment):
        reply = await generator.generate_reply(analyzed_comment)
        assert reply.suggested_text is not None
        assert len(reply.suggested_text) > 0
        assert reply.confidence_score > 0
        assert reply.comment_id == analyzed_comment.id
        assert reply.organization_id == analyzed_comment.organization_id

    @pytest.mark.asyncio
    async def test_generate_reply_with_template(self, generator, analyzed_comment):
        template = ReplyTemplate(
            organization_id=analyzed_comment.organization_id,
            template_text="Hi {user_name}, the price is ${price}.",
            variables=["user_name", "price"],
        )
        reply = await generator.generate_reply(analyzed_comment, template=template)
        assert "testuser" in reply.suggested_text

    @pytest.mark.asyncio
    async def test_generate_alternatives(self, generator, analyzed_comment):
        reply = await generator.generate_reply(analyzed_comment)
        assert len(reply.alternative_texts) == 2

    def test_auto_send_threshold(self, generator, analyzed_comment):
        reply = AutoReply(
            organization_id=analyzed_comment.organization_id,
            comment_id=analyzed_comment.id,
            suggested_text="Test reply",
            confidence_score=0.9,
            relevance_score=0.9,
            brand_voice_score=0.9,
            safety_score=0.96,
        )
        assert reply.can_auto_send(0.85) is True

        reply.confidence_score = 0.8
        assert reply.can_auto_send(0.85) is False


# --- ReplyTemplateManager Tests ---

class TestReplyTemplateManager:
    @pytest.fixture
    def manager(self):
        return ReplyTemplateManager()

    def test_create_template(self, manager):
        template = ReplyTemplate(
            organization_id=uuid4(),
            name="Pricing Template",
            template_text="Price is ${price}",
            variables=["price"],
        )
        created = manager.create_template(template)
        assert created.id == template.id

    def test_get_template(self, manager):
        template = ReplyTemplate(
            organization_id=uuid4(),
            name="Test",
            template_text="Test",
        )
        manager.create_template(template)
        found = manager.get_template(template.id)
        assert found is not None
        assert found.name == "Test"

    def test_find_matching_templates(self, manager):
        org_id = uuid4()
        template = ReplyTemplate(
            organization_id=org_id,
            name="Pricing Template",
            intent_triggers=[CommentIntent.PRICING],
            sentiment_triggers=[CommentSentiment.NEUTRAL],
            keyword_triggers=["price", "cost"],
            platform_triggers=[SocialPlatform.META],
            template_text="Price info here",
            is_active=True,
        )
        manager.create_template(template)

        comment = SocialComment(
            organization_id=org_id,
            platform=SocialPlatform.META,
            text="How much does this cost?",
            intent=CommentIntent.PRICING,
            sentiment=CommentSentiment.NEUTRAL,
        )

        matches = manager.find_matching_templates(comment, org_id)
        assert len(matches) == 1
        assert matches[0].name == "Pricing Template"

    def test_template_not_matching_wrong_intent(self, manager):
        org_id = uuid4()
        template = ReplyTemplate(
            organization_id=org_id,
            name="Complaint Template",
            intent_triggers=[CommentIntent.COMPLAINT],
            template_text="Sorry",
            is_active=True,
        )
        manager.create_template(template)

        comment = SocialComment(
            organization_id=org_id,
            platform=SocialPlatform.META,
            text="How much is this?",
            intent=CommentIntent.PRICING,
        )

        matches = manager.find_matching_templates(comment, org_id)
        assert len(matches) == 0


# --- SocialInboxManager Tests ---

class TestSocialInboxManager:
    @pytest.fixture
    def manager(self):
        return SocialInboxManager()

    @pytest.fixture
    def sample_comments(self):
        org_id = uuid4()
        return [
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.META,
                text="Great product!",
                sentiment=CommentSentiment.POSITIVE,
                intent=CommentIntent.PRAISE,
                posted_at=datetime.now() - timedelta(hours=1),
            ),
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.LINKEDIN,
                text="How much?",
                sentiment=CommentSentiment.NEUTRAL,
                intent=CommentIntent.PRICING,
                posted_at=datetime.now() - timedelta(hours=2),
            ),
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.META,
                text="This is terrible!",
                sentiment=CommentSentiment.NEGATIVE,
                intent=CommentIntent.COMPLAINT,
                posted_at=datetime.now() - timedelta(hours=3),
            ),
        ]

    @pytest.mark.asyncio
    async def test_process_inbox_no_filters(self, manager, sample_comments):
        inbox = SocialInbox(organization_id=sample_comments[0].organization_id)
        result = await manager.process_inbox(inbox, sample_comments)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_process_inbox_platform_filter(self, manager, sample_comments):
        inbox = SocialInbox(
            organization_id=sample_comments[0].organization_id,
            platforms=[SocialPlatform.META],
        )
        result = await manager.process_inbox(inbox, sample_comments)
        assert len(result) == 2
        assert all(c.platform == SocialPlatform.META for c in result)

    @pytest.mark.asyncio
    async def test_process_inbox_sentiment_filter(self, manager, sample_comments):
        inbox = SocialInbox(
            organization_id=sample_comments[0].organization_id,
            sentiment_filter=[CommentSentiment.POSITIVE],
        )
        result = await manager.process_inbox(inbox, sample_comments)
        assert len(result) == 1
        assert result[0].sentiment == CommentSentiment.POSITIVE

    @pytest.mark.asyncio
    async def test_process_inbox_intent_filter(self, manager, sample_comments):
        inbox = SocialInbox(
            organization_id=sample_comments[0].organization_id,
            intent_filter=[CommentIntent.COMPLAINT],
        )
        result = await manager.process_inbox(inbox, sample_comments)
        assert len(result) == 1
        assert result[0].intent == CommentIntent.COMPLAINT

    @pytest.mark.asyncio
    async def test_process_inbox_pagination(self, manager, sample_comments):
        inbox = SocialInbox(
            organization_id=sample_comments[0].organization_id,
            page=1,
            page_size=2,
        )
        result = await manager.process_inbox(inbox, sample_comments)
        assert len(result) == 2


# --- CommentAnalyticsEngine Tests ---

class TestCommentAnalyticsEngine:
    @pytest.fixture
    def engine(self):
        return CommentAnalyticsEngine()

    @pytest.fixture
    def sample_data(self):
        org_id = uuid4()
        now = datetime.now()
        comments = [
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.META,
                text="Great!",
                sentiment=CommentSentiment.POSITIVE,
                sentiment_score=0.8,
                intent=CommentIntent.PRAISE,
                like_count=10,
                reply_count=2,
                posted_at=now - timedelta(hours=1),
            ),
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.LINKEDIN,
                text="How much?",
                sentiment=CommentSentiment.NEUTRAL,
                sentiment_score=0.0,
                intent=CommentIntent.PRICING,
                like_count=5,
                reply_count=1,
                posted_at=now - timedelta(hours=2),
            ),
            SocialComment(
                organization_id=org_id,
                platform=SocialPlatform.META,
                text="Terrible!",
                sentiment=CommentSentiment.NEGATIVE,
                sentiment_score=-0.8,
                intent=CommentIntent.COMPLAINT,
                spam_score=0.3,
                toxicity_score=0.7,
                posted_at=now - timedelta(hours=3),
            ),
        ]
        replies = [
            AutoReply(
                organization_id=org_id,
                comment_id=comments[0].id,
                suggested_text="Thanks!",
                status=ReplyStatus.SENT,
                approved_by=None,  # Auto-approved
            ),
            AutoReply(
                organization_id=org_id,
                comment_id=comments[1].id,
                suggested_text="Price is $100",
                status=ReplyStatus.SENT,
                approved_by=uuid4(),  # Human approved
            ),
        ]
        return org_id, comments, replies

    @pytest.mark.asyncio
    async def test_generate_analytics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.total_comments == 3
        assert analytics.comments_by_platform["meta"] == 2
        assert analytics.comments_by_platform["linkedin"] == 1
        assert analytics.comments_by_sentiment["positive"] == 1
        assert analytics.comments_by_sentiment["neutral"] == 1
        assert analytics.comments_by_sentiment["negative"] == 1
        assert analytics.comments_by_intent["praise"] == 1
        assert analytics.comments_by_intent["pricing"] == 1
        assert analytics.comments_by_intent["complaint"] == 1

    @pytest.mark.asyncio
    async def test_engagement_metrics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.total_likes == 15  # 10 + 5 + 0
        assert analytics.total_replies == 3  # 2 + 1 + 0
        assert analytics.avg_engagement_rate == (15 + 3 + 0) / 3

    @pytest.mark.asyncio
    async def test_response_metrics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.total_replies_sent == 2
        assert analytics.auto_replies_sent == 1
        assert analytics.manual_replies_sent == 1
        assert analytics.response_rate == 2 / 3 * 100

    @pytest.mark.asyncio
    async def test_sentiment_metrics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.positive_sentiment_pct == 1/3 * 100
        assert analytics.negative_sentiment_pct == 1/3 * 100

    @pytest.mark.asyncio
    async def test_moderation_metrics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.spam_detected == 0
        assert analytics.toxicity_flagged == 1  # One comment has toxicity_score > 0.5

    @pytest.mark.asyncio
    async def test_auto_reply_metrics(self, engine, sample_data):
        org_id, comments, replies = sample_data
        analytics = await engine.generate_analytics(
            org_id, comments, replies,
            datetime.now() - timedelta(days=1),
            datetime.now(),
        )

        assert analytics.auto_reply_generated == 2
        assert analytics.auto_reply_sent == 2
        assert analytics.auto_reply_approval_rate == 100.0


# --- SocialComment Entity Tests ---

class TestSocialComment:
    def test_to_dict(self):
        comment = SocialComment(
            id=uuid4(),
            organization_id=uuid4(),
            platform=SocialPlatform.META,
            text="Test comment",
            sentiment=CommentSentiment.POSITIVE,
        )
        d = comment.to_dict()
        assert d["platform"] == "meta"
        assert d["sentiment"] == "positive"

    def test_needs_human_review_toxic(self):
        comment = SocialComment(
            toxicity_score=0.9,
        )
        assert comment.needs_human_review() is True

    def test_needs_human_review_spam(self):
        comment = SocialComment(
            spam_score=0.95,
        )
        assert comment.needs_human_review() is True

    def test_needs_human_review_negative(self):
        comment = SocialComment(
            sentiment=CommentSentiment.VERY_NEGATIVE,
        )
        assert comment.needs_human_review() is True

    def test_needs_human_review_normal(self):
        comment = SocialComment(
            sentiment=CommentSentiment.NEUTRAL,
            spam_score=0.1,
            toxicity_score=0.1,
        )
        assert comment.needs_human_review() is False


# --- AutoReply Entity Tests ---

class TestAutoReply:
    def test_can_auto_send_high_confidence(self):
        reply = AutoReply(
            confidence_score=0.9,
            relevance_score=0.9,
            brand_voice_score=0.9,
            safety_score=0.96,
            status=ReplyStatus.PENDING,
        )
        assert reply.can_auto_send(0.85) is True

    def test_can_auto_send_low_confidence(self):
        reply = AutoReply(
            confidence_score=0.7,
            relevance_score=0.9,
            brand_voice_score=0.9,
            safety_score=0.96,
            status=ReplyStatus.PENDING,
        )
        assert reply.can_auto_send(0.85) is False

    def test_can_auto_send_wrong_status(self):
        reply = AutoReply(
            confidence_score=0.9,
            relevance_score=0.9,
            brand_voice_score=0.9,
            safety_score=0.96,
            status=ReplyStatus.SENT,
        )
        assert reply.can_auto_send(0.85) is False


# --- ReplyTemplate Entity Tests ---

class TestReplyTemplate:
    def test_to_dict(self):
        template = ReplyTemplate(
            id=uuid4(),
            organization_id=uuid4(),
            name="Test",
            template_text="Hello {name}",
            variables=["name"],
        )
        d = template.to_dict()
        assert d["name"] == "Test"
        assert "name" in d["variables"]


# --- CommentAnalytics Entity Tests ---

class TestCommentAnalytics:
    def test_to_dict(self):
        analytics = CommentAnalytics(
            organization_id=uuid4(),
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_comments=100,
        )
        d = analytics.to_dict()
        assert d["total_comments"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
