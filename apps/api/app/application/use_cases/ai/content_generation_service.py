from app.application.use_cases.ai.prompt_manager import PromptManager
from app.domain.entities.content.brand_voice import BrandVoice
from app.domain.entities.content.content_template import ContentTemplate
from app.infrastructure.external_adapters.ai.router import AIRouter

BUILTIN_TEMPLATES = [
    ContentTemplate(
        name="Blog Post",
        content_type="blog",
        description="A standard blog post with title, introduction, body sections, and conclusion",
        sections=[
            {"name": "title", "prompt": "Write a compelling blog title about {topic}"},
            {"name": "introduction", "prompt": "Write an engaging introduction that hooks the reader"},
            {"name": "body", "prompt": "Write the main body covering {key_points}"},
            {"name": "conclusion", "prompt": "Write a conclusion with a call to action"},
        ],
        variables=["topic", "key_points"],
        is_builtin=True,
    ),
    ContentTemplate(
        name="Social Post",
        content_type="social",
        description="A short social media post with hook, body, and hashtags",
        sections=[
            {"name": "hook", "prompt": "Write an attention-grabbing hook"},
            {"name": "body", "prompt": "Write the main message"},
            {"name": "hashtags", "prompt": "Suggest 3-5 relevant hashtags"},
        ],
        variables=["topic", "platform"],
        is_builtin=True,
    ),
    ContentTemplate(
        name="Email Newsletter",
        content_type="email",
        description="A marketing email with subject line, greeting, body, and CTA",
        sections=[
            {"name": "subject", "prompt": "Write a compelling subject line"},
            {"name": "greeting", "prompt": "Write a warm greeting"},
            {"name": "body", "prompt": "Write the main content about {topic}"},
            {"name": "cta", "prompt": "Write a clear call to action"},
        ],
        variables=["topic", "audience"],
        is_builtin=True,
    ),
    ContentTemplate(
        name="Ad Copy",
        content_type="ad",
        description="A short ad copy with headline, description, and CTA",
        sections=[
            {"name": "headline", "prompt": "Write a short, punchy headline (max 40 chars)"},
            {"name": "description", "prompt": "Write a compelling description (max 125 chars)"},
            {"name": "cta", "prompt": "Write a strong call to action"},
        ],
        variables=["product", "audience"],
        is_builtin=True,
    ),
]


class ContentGenerationService:
    def __init__(self, router: AIRouter | None = None, prompt_manager: PromptManager | None = None):
        self.router = router or AIRouter()
        self.prompt_manager = prompt_manager or PromptManager()

    async def generate(
        self,
        template: ContentTemplate,
        variables: dict[str, str],
        brand_voice: BrandVoice | None = None,
        tone: str | None = None,
        instructions: str = "",
    ) -> dict:
        system_prompt = await self._build_system_prompt(template, brand_voice, tone, instructions)
        user_prompt = self._build_user_prompt(template, variables)

        response = await self.router.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        sections = self._parse_sections(response, template.sections)

        return {
            "content": response,
            "sections": sections,
            "template_name": template.name,
            "content_type": template.content_type,
        }

    async def rewrite(
        self,
        content: str,
        tone: str | None = None,
        brand_voice: BrandVoice | None = None,
        instructions: str = "",
    ) -> str:
        voice_context = ""
        if brand_voice:
            voice_context = (
                f"Brand voice: {brand_voice.name}\n"
                f"Tone: {brand_voice.tone}\n"
                f"Style: {brand_voice.style_guide}\n"
                f"Vocabulary: {', '.join(brand_voice.vocabulary)}\n"
            )

        target_tone = f"Target tone: {tone}" if tone else ""
        system = await self.prompt_manager.get_prompt(
            "content_rewriter",
            variables={
                "voice_context": voice_context,
                "instructions": instructions,
                "target_tone": target_tone,
            },
        )

        return await self.router.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": f"Rewrite this content:\n\n{content}"},
        ])

    async def generate_bulk(
        self,
        template: ContentTemplate,
        variable_rows: list[dict[str, str]],
        brand_voice: BrandVoice | None = None,
        tone: str | None = None,
    ) -> list[dict]:
        results = []
        for i, row in enumerate(variable_rows):
            result = await self.generate(template, row, brand_voice, tone)
            result["row_index"] = i
            result["variables"] = row
            results.append(result)
        return results

    async def _build_system_prompt(
        self,
        template: ContentTemplate,
        brand_voice: BrandVoice | None = None,
        tone: str | None = None,
        instructions: str = "",
    ) -> str:
        brand_voice_section = ""
        if brand_voice:
            brand_voice_section = (
                f"Brand Voice: {brand_voice.name}\n"
                f"Tone: {tone or brand_voice.tone}\n"
                f"Style Guide: {brand_voice.style_guide}\n"
                f"Target Audience: {brand_voice.target_audience}\n"
                f"Preferred Vocabulary: {', '.join(brand_voice.vocabulary)}\n"
            )
        elif tone:
            brand_voice_section = f"Tone: {tone}\n"

        return await self.prompt_manager.get_prompt(
            "content_writer",
            variables={
                "template_guidance": template.system_prompt or "",
                "content_type": template.content_type,
                "sections": ", ".join(s["name"] for s in template.sections),
                "brand_voice": brand_voice_section,
                "instructions": instructions or "",
            },
        )

    def _build_user_prompt(self, template: ContentTemplate, variables: dict[str, str]) -> str:
        prompt = f"Generate a {template.content_type} using the template '{template.name}'.\n\n"
        if variables:
            prompt += "Variables:\n"
            for k, v in variables.items():
                prompt += f"  {k}: {v}\n"
        prompt += (
            "\nSections to generate:\n"
            + "\n".join(f"  - {s['name']}: {s['prompt']}" for s in template.sections)
        )
        return prompt

    def _parse_sections(self, content: str, sections: list[dict]) -> dict:
        result = {}
        for section in sections:
            name = section["name"]
            marker = f"## {name}"
            if marker in content:
                parts = content.split(marker, 1)
                if len(parts) > 1:
                    remaining = parts[1].strip()
                    next_marker = remaining.find("\n## ")
                    if next_marker != -1:
                        result[name] = remaining[:next_marker].strip()
                    else:
                        result[name] = remaining
        return result
