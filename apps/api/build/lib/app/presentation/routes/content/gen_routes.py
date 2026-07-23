from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.ai.content_generation_service import (
    ContentGenerationService,
)
from app.application.use_cases.ai.prompt_manager import PromptManager
from app.application.use_cases.ai.seo_scorer import SEOScorer
from app.domain.common import now
from app.infrastructure.db.repositories.brand_voice_repository import BrandVoiceRepository
from app.infrastructure.db.repositories.content_template_repository import ContentTemplateRepository
from app.infrastructure.db.repositories.prompt_repository import SystemPromptRepositoryImpl
from app.presentation.dependencies import get_db, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import PaginatedResponse, SuccessResponse


async def _get_content_service(db: AsyncSession) -> ContentGenerationService:
    prompt_repo = SystemPromptRepositoryImpl(db)
    prompt_manager = PromptManager(repository=prompt_repo)
    return ContentGenerationService(prompt_manager=prompt_manager)


router = APIRouter()


class GenerateRequest(BaseModel):
    organization_id: UUID
    template_id: UUID
    variables: dict[str, str] = {}
    brand_voice_id: UUID | None = None
    tone: str | None = None
    instructions: str = ""


class RewriteRequest(BaseModel):
    organization_id: UUID
    content: str
    tone: str | None = None
    brand_voice_id: UUID | None = None
    instructions: str = ""


class BulkGenerateRequest(BaseModel):
    organization_id: UUID
    template_id: UUID
    variable_rows: list[dict[str, str]]
    brand_voice_id: UUID | None = None
    tone: str | None = None


class SEOScoreRequest(BaseModel):
    content: str
    target_keywords: list[str] = []


class BrandVoiceCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    tone: str = "professional"
    vocabulary: list[str] = []
    style_guide: str = ""
    target_audience: str = ""


class BrandVoiceUpdate(BaseModel):
    name: str | None = None
    tone: str | None = None
    vocabulary: list[str] | None = None
    style_guide: str | None = None
    target_audience: str | None = None
    is_active: bool | None = None


class TemplateCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    content_type: str = "blog"
    description: str = ""
    sections: list[dict] = []
    variables: list[str] = []
    system_prompt: str = ""


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sections: list[dict] | None = None
    variables: list[str] | None = None
    system_prompt: str | None = None


@router.post("/ai/content/generate", summary="Generate AI content")
async def generate_content(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    await require_feature("ai_content_generation", request.organization_id, "auto", db)
    service = await _get_content_service(db)
    template_repo = ContentTemplateRepository(db)
    voice_repo = BrandVoiceRepository(db)

    template = await template_repo.find_by_id(request.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    brand_voice = None
    if request.brand_voice_id:
        brand_voice = await voice_repo.find_by_id(request.brand_voice_id)
        if brand_voice is None:
            raise HTTPException(status_code=404, detail="Brand voice not found")

    result = await service.generate(
        template=template,
        variables=request.variables,
        brand_voice=brand_voice,
        tone=request.tone,
        instructions=request.instructions,
    )
    return SuccessResponse(data=result)


@router.post("/ai/content/rewrite", summary="Rewrite content with AI")
async def rewrite_content(
    request: RewriteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = await _get_content_service(db)
    voice_repo = BrandVoiceRepository(db)

    brand_voice = None
    if request.brand_voice_id:
        brand_voice = await voice_repo.find_by_id(request.brand_voice_id)
        if brand_voice is None:
            raise HTTPException(status_code=404, detail="Brand voice not found")

    result = await service.rewrite(
        content=request.content,
        tone=request.tone,
        brand_voice=brand_voice,
        instructions=request.instructions,
    )

    return SuccessResponse(data={"content": result})


@router.post("/ai/content/generate/bulk", summary="Bulk generate AI content")
async def bulk_generate(
    request: BulkGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = await _get_content_service(db)
    template_repo = ContentTemplateRepository(db)
    voice_repo = BrandVoiceRepository(db)

    template = await template_repo.find_by_id(request.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    brand_voice = None
    if request.brand_voice_id:
        brand_voice = await voice_repo.find_by_id(request.brand_voice_id)

    results = await service.generate_bulk(
        template=template,
        variable_rows=request.variable_rows,
        brand_voice=brand_voice,
        tone=request.tone,
    )

    return SuccessResponse(data={"results": results, "total": len(results)})


@router.post("/ai/content/seo-score", summary="Score content for SEO")
async def score_content(
    request: SEOScoreRequest,
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    scorer = SEOScorer()
    return SuccessResponse(data=scorer.score(request.content, request.target_keywords))


@router.post("/brand-voices", status_code=201, summary="Create a brand voice")
async def create_brand_voice(
    request: BrandVoiceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    from app.domain.entities.content.brand_voice import BrandVoice

    voice = BrandVoice.create(
        organization_id=request.organization_id,
        name=request.name,
        tone=request.tone,
        vocabulary=request.vocabulary,
        style_guide=request.style_guide,
        target_audience=request.target_audience,
        created_by=user_id,
    )
    repo = BrandVoiceRepository(db)
    saved = await repo.save(voice)
    return SuccessResponse(
        data={
            "id": str(saved.id),
            "name": saved.name,
            "tone": saved.tone,
            "is_active": saved.is_active,
        }
    )


@router.get("/brand-voices", summary="List brand voices")
async def list_brand_voices(
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    repo = BrandVoiceRepository(db)
    voices = await repo.find_by_organization(organization_id)
    items = [
        {
            "id": str(v.id),
            "name": v.name,
            "tone": v.tone,
            "style_guide": v.style_guide[:100] if v.style_guide else "",
            "target_audience": v.target_audience[:100] if v.target_audience else "",
            "is_active": v.is_active,
            "vocabulary": v.vocabulary,
            "created_at": v.created_at.isoformat(),
        }
        for v in voices
    ]
    total = len(items)
    page = pagination["page"]
    limit = pagination["limit"]
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    )


@router.patch("/brand-voices/{voice_id}", summary="Update a brand voice")
async def update_brand_voice(
    voice_id: UUID,
    request: BrandVoiceUpdate,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(organization_id, "member", user_id, db)
    repo = BrandVoiceRepository(db)
    voice = await repo.find_by_id(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail="Brand voice not found")
    if str(voice.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Brand voice not found")
    if request.name is not None:
        voice.name = request.name
    if request.tone is not None:
        voice.tone = request.tone
    if request.vocabulary is not None:
        voice.vocabulary = request.vocabulary
    if request.style_guide is not None:
        voice.style_guide = request.style_guide
    if request.target_audience is not None:
        voice.target_audience = request.target_audience
    if request.is_active is not None:
        voice.is_active = request.is_active
        voice.updated_at = now()
    saved = await repo.save(voice)
    return SuccessResponse(
        data={
            "id": str(saved.id),
            "name": saved.name,
            "tone": saved.tone,
            "is_active": saved.is_active,
        }
    )


@router.delete("/brand-voices/{voice_id}", status_code=204, summary="Delete a brand voice")
async def delete_brand_voice(
    voice_id: UUID,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    repo = BrandVoiceRepository(db)
    voice = await repo.find_by_id(voice_id)
    if not voice or str(voice.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Brand voice not found") from None
    await repo.delete(voice_id)


@router.post("/content/templates", status_code=201, summary="Create a content template")
async def create_template(
    request: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    from app.domain.entities.content.content_template import ContentTemplate

    template = ContentTemplate.create(
        organization_id=request.organization_id,
        name=request.name,
        content_type=request.content_type,
        description=request.description,
        sections=request.sections,
        variables=request.variables,
        system_prompt=request.system_prompt,
        created_by=user_id,
    )
    repo = ContentTemplateRepository(db)
    saved = await repo.save(template)
    return SuccessResponse(
        data={
            "id": str(saved.id),
            "name": saved.name,
            "content_type": saved.content_type,
        }
    )


@router.get("/content/templates", summary="List content templates")
async def list_templates(
    organization_id: UUID = Query(...),
    include_builtin: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    repo = ContentTemplateRepository(db)
    org_templates = await repo.find_by_organization(organization_id)
    builtin = await repo.find_builtin() if include_builtin else []
    all_templates = builtin + org_templates
    seen = set()
    unique = []
    for t in all_templates:
        if t.id not in seen:
            seen.add(t.id)
            unique.append(t)
    items = [
        {
            "id": str(t.id),
            "name": t.name,
            "content_type": t.content_type,
            "description": t.description,
            "sections": t.sections,
            "variables": t.variables,
            "is_builtin": t.is_builtin,
            "created_at": t.created_at.isoformat(),
        }
        for t in unique
    ]
    total = len(items)
    page = pagination["page"]
    limit = pagination["limit"]
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    )


@router.get("/content/templates/{template_id}", summary="Get a content template")
async def get_template(
    template_id: UUID,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(organization_id, "viewer", user_id, db)
    repo = ContentTemplateRepository(db)
    template = await repo.find_by_id(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return SuccessResponse(
        data={
            "id": str(template.id),
            "name": template.name,
            "content_type": template.content_type,
            "description": template.description,
            "sections": template.sections,
            "variables": template.variables,
            "system_prompt": template.system_prompt,
            "is_builtin": template.is_builtin,
            "created_at": template.created_at.isoformat(),
        }
    )


@router.patch("/content/templates/{template_id}", summary="Update a content template")
async def update_template(
    template_id: UUID,
    request: TemplateUpdate,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SuccessResponse:
    await require_org_role(organization_id, "member", user_id, db)
    repo = ContentTemplateRepository(db)
    template = await repo.find_by_id(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if str(template.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Template not found")
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.sections is not None:
        template.sections = request.sections
    if request.variables is not None:
        template.variables = request.variables
    if request.system_prompt is not None:
        template.system_prompt = request.system_prompt
        template.updated_at = now()
    saved = await repo.save(template)
    return SuccessResponse(
        data={
            "id": str(saved.id),
            "name": saved.name,
            "updated": True,
        }
    )


@router.delete(
    "/content/templates/{template_id}", status_code=204, summary="Delete a content template"
)
async def delete_template(
    template_id: UUID,
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> None:
    await require_org_role(organization_id, "admin", user_id, db)
    repo = ContentTemplateRepository(db)
    template = await repo.find_by_id(template_id)
    if not template or str(template.organization_id) != str(organization_id):
        raise HTTPException(status_code=404, detail="Template not found") from None
    await repo.delete(template_id)
