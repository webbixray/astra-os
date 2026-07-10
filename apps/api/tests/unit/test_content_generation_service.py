from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.ai.content_generation_service import (
    BUILTIN_TEMPLATES,
    ContentGenerationService,
)
from app.domain.entities.content.brand_voice import BrandVoice
from app.domain.entities.content.content_template import ContentTemplate


@pytest.fixture
def mock_router():
    router = MagicMock()
    router.chat = AsyncMock(return_value="Mocked content response")
    return router


@pytest.fixture
def blog_template():
    return BUILTIN_TEMPLATES[0]


@pytest.fixture
def service(mock_router):
    return ContentGenerationService(router=mock_router)


class TestContentGenerationService:
    async def test_generate_returns_expected_structure(self, service, mock_router, blog_template):
        result = await service.generate(blog_template, {"topic": "AI", "key_points": "benefits"})
        assert result["content"] == "Mocked content response"
        assert result["template_name"] == "Blog Post"
        assert result["content_type"] == "blog"
        assert isinstance(result["sections"], dict)
        mock_router.chat.assert_awaited_once()

    async def test_generate_with_brand_voice(self, service, mock_router):
        bv = BrandVoice(
            name="TechBrand",
            tone="professional",
            vocabulary=["innovative", "scalable"],
            style_guide="Use short sentences",
        )
        template = BUILTIN_TEMPLATES[1]
        result = await service.generate(template, {"topic": "Tech", "platform": "LinkedIn"}, brand_voice=bv)
        assert result["content"] == "Mocked content response"
        mock_router.chat.assert_awaited_once()

    async def test_generate_with_tone(self, service, mock_router, blog_template):
        result = await service.generate(blog_template, {"topic": "AI"}, tone="casual")
        assert result["content_type"] == "blog"
        mock_router.chat.assert_awaited_once()

    async def test_rewrite(self, service, mock_router):
        result = await service.rewrite("Original content", tone="professional")
        assert result == "Mocked content response"
        mock_router.chat.assert_awaited_once()

    async def test_rewrite_with_brand_voice(self, service, mock_router):
        bv = BrandVoice(name="MyBrand", tone="friendly", vocabulary=["awesome"])
        result = await service.rewrite("Original content", brand_voice=bv, instructions="Make it shorter")
        assert result == "Mocked content response"
        mock_router.chat.assert_awaited_once()

    async def test_generate_bulk(self, service, mock_router, blog_template):
        rows = [
            {"topic": "AI", "key_points": "benefits"},
            {"topic": "Blockchain", "key_points": "security"},
        ]
        results = await service.generate_bulk(blog_template, rows)
        assert len(results) == 2
        assert results[0]["row_index"] == 0
        assert results[1]["row_index"] == 1
        assert mock_router.chat.await_count == 2

    async def test_build_system_prompt_without_brand_voice(self, service):
        template = ContentTemplate(
            name="Test", content_type="blog",
            sections=[{"name": "title", "prompt": "Write a title"}],
        )
        prompt = await service._build_system_prompt(template)
        assert "Content type: blog" in prompt
        assert "Sections to generate: title" in prompt

    async def test_build_system_prompt_with_brand_voice(self, service):
        template = BUILTIN_TEMPLATES[0]
        bv = BrandVoice(name="Brand", tone="casual", vocabulary=["cool"])
        prompt = await service._build_system_prompt(template, brand_voice=bv)
        assert "Brand Voice: Brand" in prompt
        assert "Tone: casual" in prompt
        assert "Vocabulary: cool" in prompt

    async def test_build_system_prompt_with_instructions(self, service):
        template = BUILTIN_TEMPLATES[0]
        prompt = await service._build_system_prompt(template, instructions="Keep it under 100 words")
        assert "Keep it under 100 words" in prompt

    def test_build_user_prompt(self, service, blog_template):
        prompt = service._build_user_prompt(blog_template, {"topic": "AI"})
        assert "topic: AI" in prompt
        assert "Generate a blog" in prompt

    def test_build_user_prompt_no_variables(self, service):
        template = ContentTemplate(name="Test", content_type="social", sections=[])
        prompt = service._build_user_prompt(template, {})
        assert "Generate a social" in prompt

    def test_parse_sections_found(self, service):
        content = "## title\nMy Title\n## body\nMy Body"
        sections = [
            {"name": "title", "prompt": "Write title"},
            {"name": "body", "prompt": "Write body"},
        ]
        result = service._parse_sections(content, sections)
        assert result["title"] == "My Title"
        assert result["body"] == "My Body"

    def test_parse_sections_missing(self, service):
        content = "Some content without section markers"
        sections = [{"name": "title", "prompt": "Write title"}]
        result = service._parse_sections(content, sections)
        assert result == {}
