from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.ai.manage_prompts_use_case import ManagePromptsUseCase
from app.application.use_cases.ai.prompt_manager import BUILTIN_PROMPTS, PromptManager
from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt
from app.infrastructure.db.repositories.prompt_repository import SystemPromptRepositoryImpl
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class PromptResponse(BaseModel):
    id: UUID
    org_id: UUID | None = None
    name: str
    description: str
    category: str
    content: str
    variables: list[str]
    version: int
    status: str
    is_builtin: bool
    created_by: UUID | None = None
    created_at: str
    updated_at: str


class CreatePromptRequest(BaseModel):
    name: str
    content: str
    description: str = ""
    category: str = "system"
    org_id: UUID | None = None
    variables: list[str] = []


class UpdatePromptRequest(BaseModel):
    content: str | None = None
    description: str | None = None
    variables: list[str] | None = None
    status: str | None = None


def _to_response(prompt: SystemPrompt) -> PromptResponse:
    return PromptResponse(
        id=prompt.id,
        org_id=prompt.org_id,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        content=prompt.content,
        variables=prompt.variables,
        version=prompt.version,
        status=prompt.status.value,
        is_builtin=prompt.is_builtin,
        created_by=prompt.created_by,
        created_at=prompt.created_at.isoformat(),
        updated_at=prompt.updated_at.isoformat(),
    )


async def get_prompt_manager(db: AsyncSession = Depends(get_db)) -> PromptManager:
    repo = SystemPromptRepositoryImpl(db)
    return PromptManager(repository=repo)


async def get_manage_use_case(
    manager: PromptManager = Depends(get_prompt_manager),
) -> ManagePromptsUseCase:
    return ManagePromptsUseCase(manager)


@router.get("/prompts", summary="List all prompts")
async def list_prompts(
    category: str | None = None,
    org_id: UUID | None = None,
    use_case: ManagePromptsUseCase = Depends(get_manage_use_case),
    _user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[PromptResponse]:
    if org_id:
        await require_org_role(org_id, "viewer", _user_id, db)
    prompts = await use_case.list_prompts(org_id=org_id, category=category)
    return [_to_response(p) for p in prompts]


@router.get("/prompts/builtins", summary="List built-in prompts")
async def list_builtins() -> list[dict]:
    return [
        {
            "name": name,
            "description": data["description"],
            "category": data["category"].value,
            "variables": data.get("variables", []),
        }
        for name, data in BUILTIN_PROMPTS.items()
    ]


@router.get("/prompts/{prompt_id}", summary="Get prompt by ID")
async def get_prompt(
    prompt_id: UUID,
    organization_id: UUID = Query(...),
    use_case: ManagePromptsUseCase = Depends(get_manage_use_case),
    _user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    await require_org_role(organization_id, "viewer", _user_id, db)
    prompt = await use_case.get_prompt(prompt_id)
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return _to_response(prompt)


@router.post("/prompts", status_code=status.HTTP_201_CREATED, summary="Create a new prompt")
async def create_prompt(
    request: CreatePromptRequest,
    use_case: ManagePromptsUseCase = Depends(get_manage_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    if request.org_id:
        await require_org_role(request.org_id, "member", user_id, db)
    try:
        category = PromptCategory(request.category)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid category: {request.category}") from None
    prompt = await use_case.create_prompt(
        name=request.name,
        content=request.content,
        category=category,
        description=request.description,
        org_id=request.org_id,
        variables=request.variables,
        created_by=user_id,
    )
    return _to_response(prompt)


@router.patch("/prompts/{prompt_id}", summary="Update a prompt")
async def update_prompt(
    prompt_id: UUID,
    request: UpdatePromptRequest,
    organization_id: UUID = Query(...),
    use_case: ManagePromptsUseCase = Depends(get_manage_use_case),
    _user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    await require_org_role(organization_id, "member", _user_id, db)
    status_enum = None
    if request.status is not None:
        try:
            status_enum = PromptStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid status: {request.status}") from None
    try:
        prompt = await use_case.update_prompt(
            prompt_id=prompt_id,
            content=request.content,
            description=request.description,
            variables=request.variables,
            status=status_enum,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
    return _to_response(prompt)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a prompt")
async def delete_prompt(
    prompt_id: UUID,
    organization_id: UUID = Query(...),
    use_case: ManagePromptsUseCase = Depends(get_manage_use_case),
    _user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(organization_id, "admin", _user_id, db)
    await use_case.delete_prompt(prompt_id)
