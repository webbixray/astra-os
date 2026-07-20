"""Tests for content generation routes API endpoints."""

import hashlib
import hmac
import secrets
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.application.use_cases.ai.content_generation_service import ContentGenerationService
from app.application.use_cases.ai.prompt_manager import PromptManager
from app.application.use_cases.ai.seo_scorer import SEOScorer
from app.domain.entities.content.brand_voice import BrandVoice
from app.domain.entities.content.content_template import ContentTemplate
from app.main import create_app
from app.presentation.dependencies import get_db, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role
from app.presentation.routes.content.gen_routes import (
    _get_content_service,
    router,
)


def _mock_template(**kwargs):
    """Create a mock content template."""
    t = MagicMock(spec=ContentTemplate)
    t.id = kwargs.get("id", uuid4())
    t.organization_id = kwargs.get("organization_id", uuid4())
    t.name = kwargs.get("name", "Test Template")
    t.content_type = kwargs.get("content_type", "blog")
    t.description = kwargs.get("description", "Test Description")
    t.sections = kwargs.get("sections", [])
    t.variables = kwargs.get("variables", ["topic"])
    t.system_prompt = kwargs.get("system_prompt", "Write about {topic}")
    t.is_builtin = kwargs.get("is_builtin", False)
    t.created_at = kwargs.get("created_at", datetime.now())
    return t


def _mock_brand_voice(**kwargs):
    """Create a mock brand voice."""
    b = MagicMock(spec=BrandVoice)
    b.id = kwargs.get("id", uuid4())
    b.organization_id = kwargs.get("organization_id", uuid4())
    b.name = kwargs.get("name", "Test Voice")
    b.tone = kwargs.get("tone", "professional")
    b.vocabulary = kwargs.get("vocabulary", [])
    b.style_guide = kwargs.get("style_guide", "")
    b.target_audience = kwargs.get("target_audience", "")
    b.is_active = kwargs.get("is_active", True)
    b.created_at = kwargs.get("created_at", datetime.now())
    b.updated_at = kwargs.get("updated_at", datetime.now())
    return b


def _mock_generated_content(**kwargs):
    """Create mock generated content."""
    c = MagicMock()
    c.content = kwargs.get("content", "Generated content about topic")
    c.tokens_used = kwargs.get("tokens_used", 100)
    c.cost_usd = kwargs.get("cost_usd", 0.001)
    c.model = kwargs.get("model", "gpt-4")
    return c


def _mock_seo_score(**kwargs):
    """Create mock SEO score."""
    s = MagicMock()
    s.score = kwargs.get("score", 85)
    s.suggestions = kwargs.get("suggestions", ["Add more keywords"])
    s.word_count = kwargs.get("word_count", 500)
    s.keyword_density = kwargs.get("keyword_density", {})
    return s


def _setup_csrf(test_client: AsyncClient):
    """Setup CSRF headers for test client."""
    from app.config import config
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    test_client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
    return {"X-CSRF-Token": csrf_token}


@pytest.fixture
def test_app() -> FastAPI:
    """Create test app with mocked dependencies."""
    a = create_app()

    # Mock DB session
    mock_member = MagicMock()
    mock_member.role = "owner"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_member)

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    async def mock_get_db():
        yield mock_session

    a.dependency_overrides[get_db] = mock_get_db

    # Fixed user ID for auth
    fixed_user_id = uuid4()
    a.dependency_overrides[require_user_id] = lambda: fixed_user_id
    a.dependency_overrides[require_org_role] = lambda *args, **kwargs: None
    a.dependency_overrides[require_feature] = lambda *args, **kwargs: None

    # Pagination
    a.dependency_overrides[pagination_params] = lambda: {"page": 1, "limit": 20}

    yield a
    a.dependency_overrides.clear()


@pytest.fixture
async def test_client(test_app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


# ============================================================
# CONTENT GENERATION TESTS
# ============================================================

class TestContentGenerate:
    @pytest.mark.asyncio
    async def test_generate_content_success(self, test_app: FastAPI, test_client: AsyncClient):
        """Test successful content generation."""
        user_id = uuid4()
        org_id = uuid4()
        template_id = uuid4()

        mock_template = _mock_template(id=template_id, organization_id=org_id)
        mock_brand_voice = _mock_brand_voice(id=uuid4(), organization_id=org_id)
        mock_content = {"content": "Generated blog post about AI", "model": "gpt-4", "tokens_used": 100, "cost_usd": 0.001}

        # Mock the content service
        mock_service = MagicMock()
        mock_service.generate = AsyncMock(return_value=mock_content)

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_template_repo = AsyncMock()
            mock_template_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_template_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=mock_brand_voice)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/generate",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variables": {"topic": "AI in Marketing"},
                    "brand_voice_id": str(mock_brand_voice.id),
                    "tone": "professional",
                    "instructions": "Focus on ROI",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "generated" in str(data).lower()

    @pytest.mark.asyncio
    async def test_generate_content_template_not_found(self, test_app: FastAPI, test_client: AsyncClient):
        """Test content generation with non-existent template."""
        org_id = uuid4()
        template_id = uuid4()

        mock_service = MagicMock()
        mock_service.generate = AsyncMock()

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_template_repo = AsyncMock()
            mock_template_repo.find_by_id = AsyncMock(return_value=None)
            mock_template_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=None)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/generate",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variables": {"topic": "Test"},
                },
                headers=csrf_headers,
            )

        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_generate_content_brand_voice_not_found(self, test_app: FastAPI, test_client: AsyncClient):
        """Test content generation with non-existent brand voice."""
        org_id = uuid4()
        template_id = uuid4()
        brand_voice_id = uuid4()

        mock_template = _mock_template(id=template_id, organization_id=org_id)
        mock_service = MagicMock()
        mock_service.generate = AsyncMock()

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_template_repo = AsyncMock()
            mock_template_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_template_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=None)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/generate",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variables": {"topic": "Test"},
                    "brand_voice_id": str(brand_voice_id),
                },
                headers=csrf_headers,
            )

        assert response.status_code == 404
        data = response.json()
        assert "Brand voice not found" in data["detail"]


class TestContentRewrite:
    @pytest.mark.asyncio
    async def test_rewrite_content_success(self, test_app: FastAPI, test_client: AsyncClient):
        """Test successful content rewriting."""
        org_id = uuid4()
        mock_brand_voice = _mock_brand_voice(id=uuid4(), organization_id=org_id)
        mock_content = {"content": "Rewritten content with better tone"}

        mock_service = MagicMock()
        mock_service.rewrite = AsyncMock(return_value=mock_content)

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=mock_brand_voice)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/rewrite",
                json={
                    "organization_id": str(org_id),
                    "content": "Original content to rewrite",
                    "tone": "casual",
                    "brand_voice_id": str(mock_brand_voice.id),
                    "instructions": "Make it more engaging",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_rewrite_content_without_brand_voice(self, test_app: FastAPI, test_client: AsyncClient):
        """Test content rewriting without brand voice."""
        org_id = uuid4()
        mock_content = {"content": "Rewritten content"}

        mock_service = MagicMock()
        mock_service.rewrite = AsyncMock(return_value=mock_content)

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service):
            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/rewrite",
                json={
                    "organization_id": str(org_id),
                    "content": "Original content",
                    "tone": "professional",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 200


class TestBulkGenerate:
    @pytest.mark.asyncio
    async def test_bulk_generate_success(self, test_app: FastAPI, test_client: AsyncClient):
        """Test successful bulk content generation."""
        org_id = uuid4()
        template_id = uuid4()

        mock_template = _mock_template(id=template_id, organization_id=org_id)
        mock_results = [
            {"content": f"Generated content {i}", "model": "gpt-4", "tokens_used": 100, "cost_usd": 0.001}
            for i in range(3)
        ]

        mock_service = MagicMock()
        mock_service.generate_bulk = AsyncMock(return_value=mock_results)

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_template_repo = AsyncMock()
            mock_template_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_template_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=None)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/generate/bulk",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variable_rows": [
                        {"topic": "AI in Marketing"},
                        {"topic": "Content Strategy"},
                        {"topic": "SEO Best Practices"},
                    ],
                    "tone": "professional",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_bulk_generate_template_not_found(self, test_app: FastAPI, test_client: AsyncClient):
        """Test bulk generation with non-existent template."""
        org_id = uuid4()
        template_id = uuid4()

        mock_service = MagicMock()

        with patch("app.presentation.routes.content.gen_routes._get_content_service",
                   return_value=mock_service) as mock_get_service, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_class:

            mock_template_repo = AsyncMock()
            mock_template_repo.find_by_id = AsyncMock(return_value=None)
            mock_template_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.find_by_id = AsyncMock(return_value=None)
            mock_voice_class.return_value = mock_voice_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/ai/content/generate/bulk",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variable_rows": [{"topic": "Test"}],
                },
                headers=csrf_headers,
            )

        assert response.status_code == 404


class TestSEOScore:
    @pytest.mark.asyncio
    async def test_score_content_success(self, test_app: FastAPI, test_client: AsyncClient):
        """Test successful SEO scoring."""
        mock_scorer = MagicMock()
        mock_scorer.score = MagicMock(return_value={
            "score": 85,
            "suggestions": ["Add more keywords", "Increase word count"],
            "word_count": 500,
            "keyword_density": {"marketing": 2.5, "AI": 1.8},
        })

        with patch("app.presentation.routes.content.gen_routes.SEOScorer",
                   return_value=mock_scorer):
            response = await test_client.post(
                "/api/v1/ai/content/seo-score",
                json={
                    "content": "This is a test article about marketing and AI.",
                    "target_keywords": ["marketing", "AI"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert data["score"] == 85
        assert "suggestions" in data


# ============================================================
# BRAND VOICE TESTS
# ============================================================

class TestBrandVoices:
    @pytest.mark.asyncio
    async def test_create_brand_voice(self, test_app: FastAPI, test_client: AsyncClient):
        """Test creating a brand voice."""
        org_id = uuid4()
        user_id = uuid4()
        voice_id = uuid4()

        mock_voice = _mock_brand_voice(
            id=voice_id,
            organization_id=org_id,
            name="Professional Voice",
            tone="professional",
            created_by=user_id,
        )

        with patch("app.presentation.routes.content.gen_routes.BrandVoice") as mock_voice_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_repo_class:

            mock_voice_class.create = MagicMock(return_value=mock_voice)

            mock_repo = AsyncMock()
            mock_repo.save = AsyncMock(return_value=mock_voice)
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/brand-voices",
                json={
                    "organization_id": str(org_id),
                    "name": "Professional Voice",
                    "tone": "professional",
                    "vocabulary": ["marketing", "ROI", "conversion"],
                    "style_guide": "Use professional tone",
                    "target_audience": "B2B marketers",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Professional Voice"
        assert data["tone"] == "professional"

    @pytest.mark.asyncio
    async def test_list_brand_voices(self, test_app: FastAPI, test_client: AsyncClient):
        """Test listing brand voices."""
        org_id = uuid4()
        mock_voices = [
            _mock_brand_voice(id=uuid4(), organization_id=org_id, name="Voice 1", tone="professional"),
            _mock_brand_voice(id=uuid4(), organization_id=org_id, name="Voice 2", tone="casual"),
        ]

        with patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_organization = AsyncMock(return_value=mock_voices)
            mock_repo_class.return_value = mock_repo

            response = await test_client.get(
                f"/api/v1/brand-voices?organization_id={org_id}",
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_update_brand_voice(self, test_app: FastAPI, test_client: AsyncClient):
        """Test updating a brand voice."""
        org_id = uuid4()
        voice_id = uuid4()
        mock_voice = _mock_brand_voice(
            id=voice_id,
            organization_id=org_id,
            name="Original Voice",
            tone="professional",
        )

        with patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_voice)
            mock_repo.save = AsyncMock(return_value=mock_voice)
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.patch(
                f"/api/v1/brand-voices/{voice_id}",
                json={
                    "name": "Updated Voice",
                    "tone": "casual",
                },
                params={"organization_id": str(org_id)},
                headers=csrf_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Voice"
        assert data["tone"] == "casual"

    @pytest.mark.asyncio
    async def test_delete_brand_voice(self, test_app: FastAPI, test_client: AsyncClient):
        """Test deleting a brand voice."""
        org_id = uuid4()
        voice_id = uuid4()
        mock_voice = _mock_brand_voice(id=voice_id, organization_id=org_id)

        with patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_voice)
            mock_repo.delete = AsyncMock()
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.delete(
                f"/api/v1/brand-voices/{voice_id}",
                params={"organization_id": str(org_id)},
                headers=csrf_headers,
            )

        assert response.status_code == 204


# ============================================================
# CONTENT TEMPLATE TESTS
# ============================================================

class TestContentTemplates:
    @pytest.mark.asyncio
    async def test_create_template(self, test_app: FastAPI, test_client: AsyncClient):
        """Test creating a content template."""
        org_id = uuid4()
        user_id = uuid4()
        template_id = uuid4()

        mock_template = _mock_template(
            id=template_id,
            organization_id=org_id,
            name="Blog Template",
            content_type="blog",
            description="Standard blog template",
        )

        with patch("app.presentation.routes.content.gen_routes.ContentTemplate") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_repo_class:

            mock_template_class.create = MagicMock(return_value=mock_template)

            mock_repo = AsyncMock()
            mock_repo.save = AsyncMock(return_value=mock_template)
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.post(
                "/api/v1/content/templates",
                json={
                    "organization_id": str(org_id),
                    "name": "Blog Template",
                    "content_type": "blog",
                    "description": "Standard blog template",
                    "sections": [{"title": "Introduction", "type": "text"}],
                    "variables": ["topic", "audience"],
                    "system_prompt": "Write a blog about {topic} for {audience}",
                },
                headers=csrf_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Blog Template"
        assert data["content_type"] == "blog"

    @pytest.mark.asyncio
    async def test_list_templates(self, test_app: FastAPI, test_client: AsyncClient):
        """Test listing content templates."""
        org_id = uuid4()
        mock_templates = [
            _mock_template(id=uuid4(), organization_id=org_id, name="Template 1", content_type="blog"),
            _mock_template(id=uuid4(), organization_id=org_id, name="Template 2", content_type="social"),
        ]

        with patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_organization = AsyncMock(return_value=mock_templates)
            mock_repo.find_builtin = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo

            response = await test_client.get(
                f"/api/v1/content/templates?organization_id={org_id}",
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_template(self, test_app: FastAPI, test_client: AsyncClient):
        """Test getting a specific template."""
        org_id = uuid4()
        template_id = uuid4()
        mock_template = _mock_template(
            id=template_id,
            organization_id=org_id,
            name="Test Template",
            content_type="blog",
            sections=[{"title": "Intro"}],
            variables=["topic"],
            system_prompt="Write about {topic}",
        )

        with patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_repo_class.return_value = mock_repo

            response = await test_client.get(
                f"/api/v1/content/templates/{template_id}",
                params={"organization_id": str(org_id)},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(template_id)
        assert data["name"] == "Test Template"
        assert data["sections"] == [{"title": "Intro"}]

    @pytest.mark.asyncio
    async def test_update_template(self, test_app: FastAPI, test_client: AsyncClient):
        """Test updating a content template."""
        org_id = uuid4()
        template_id = uuid4()
        mock_template = _mock_template(
            id=template_id,
            organization_id=org_id,
            name="Original Template",
            content_type="blog",
        )

        with patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_repo.save = AsyncMock(return_value=mock_template)
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.patch(
                f"/api/v1/content/templates/{template_id}",
                json={
                    "name": "Updated Template",
                    "description": "Updated description",
                },
                params={"organization_id": str(org_id)},
                headers=csrf_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template"
        assert data["updated"] is True

    @pytest.mark.asyncio
    async def test_delete_template(self, test_app: FastAPI, test_client: AsyncClient):
        """Test deleting a content template."""
        org_id = uuid4()
        template_id = uuid4()
        mock_template = _mock_template(id=template_id, organization_id=org_id)

        with patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_repo.delete = AsyncMock()
            mock_repo_class.return_value = mock_repo

            csrf_headers = _setup_csrf(test_client)

            response = await test_client.delete(
                f"/api/v1/content/templates/{template_id}",
                params={"organization_id": str(org_id)},
                headers=csrf_headers,
            )

        assert response.status_code == 204


# ============================================================
# INTEGRATION TEST FOR COMPLETE FLOW
# ============================================================

class TestContentGenerationIntegration:
    @pytest.mark.asyncio
    async def test_complete_content_workflow(self, test_app: FastAPI, test_client: AsyncClient):
        """Test complete workflow: create template -> create brand voice -> generate content."""
        org_id = uuid4()
        user_id = uuid4()

        # Step 1: Create template
        template_id = uuid4()
        mock_template = _mock_template(
            id=template_id,
            organization_id=org_id,
            name="Blog Post Template",
            content_type="blog",
        )

        # Step 2: Create brand voice
        voice_id = uuid4()
        mock_voice = _mock_brand_voice(
            id=voice_id,
            organization_id=org_id,
            name="Professional Marketing",
            tone="professional",
        )

        # Step 3: Generate content
        mock_content = _mock_generated_content(
            content="Professional blog post about AI marketing strategies..."
        )

        with patch("app.presentation.routes.content.gen_routes.ContentTemplate") as mock_template_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoice") as mock_voice_class, \
             patch("app.presentation.routes.content.gen_routes.ContentTemplateRepository") as mock_template_repo_class, \
             patch("app.presentation.routes.content.gen_routes.BrandVoiceRepository") as mock_voice_repo_class, \
             patch("app.presentation.routes.content.gen_routes._get_content_service") as mock_get_service:

            mock_template_class.create = MagicMock(return_value=mock_template)
            mock_voice_class.create = MagicMock(return_value=mock_voice)

            mock_template_repo = AsyncMock()
            mock_template_repo.save = AsyncMock(return_value=mock_template)
            mock_template_repo.find_by_id = AsyncMock(return_value=mock_template)
            mock_template_repo_class.return_value = mock_template_repo

            mock_voice_repo = AsyncMock()
            mock_voice_repo.save = AsyncMock(return_value=mock_voice)
            mock_voice_repo.find_by_id = AsyncMock(return_value=mock_voice)
            mock_voice_repo_class.return_value = mock_voice_repo

            mock_service = MagicMock()
            mock_service.generate = AsyncMock(return_value=mock_content)
            mock_get_service.return_value = mock_service

            csrf_headers = _setup_csrf(test_client)

            # 1. Create template
            response = await test_client.post(
                "/api/v1/content/templates",
                json={
                    "organization_id": str(org_id),
                    "name": "Blog Post Template",
                    "content_type": "blog",
                    "description": "Template for blog posts",
                    "sections": [{"title": "Introduction", "type": "text"}],
                    "variables": ["topic", "audience"],
                    "system_prompt": "Write a professional blog about {topic} for {audience}",
                },
                headers=csrf_headers,
            )
            assert response.status_code == 201

            # 2. Create brand voice
            response = await test_client.post(
                "/api/v1/brand-voices",
                json={
                    "organization_id": str(org_id),
                    "name": "Professional Marketing",
                    "tone": "professional",
                    "vocabulary": ["strategy", "ROI", "conversion"],
                    "style_guide": "Professional, data-driven tone",
                    "target_audience": "Marketing professionals",
                },
                headers=csrf_headers,
            )
            assert response.status_code == 201

            # 3. Generate content
            response = await test_client.post(
                "/api/v1/ai/content/generate",
                json={
                    "organization_id": str(org_id),
                    "template_id": str(template_id),
                    "variables": {"topic": "AI in Marketing", "audience": "CMOs"},
                    "brand_voice_id": str(voice_id),
                    "tone": "professional",
                    "instructions": "Focus on actionable insights",
                },
                headers=csrf_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "content" in str(data).lower() or "generated" in str(data).lower()