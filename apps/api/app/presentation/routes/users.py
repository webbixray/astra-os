from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.application.use_cases.users import CreateUserUseCase, GetUserUseCase, UpdateUserUseCase
from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.presentation.dependencies import (
    get_create_user_use_case,
    get_get_user_use_case,
    get_update_user_use_case,
)
from app.presentation.middleware.auth import require_user_id
from app.presentation.schemas.common import UserResponse

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str


class UpdateUserRequest(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    user = await use_case.execute(email=request.email, name=request.name)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/{user_id}", summary="Get user by ID")
async def get_user(
    user_id: UUID,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    current_user_id: UUID = Depends(require_user_id),
) -> UserResponse:
    if user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view another user's profile") from None
    try:
        user = await use_case.execute(user_id=user_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from None
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/{user_id}", summary="Update user profile")
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    current_user_id: UUID = Depends(require_user_id),
) -> UserResponse:
    if user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user's profile") from None
    try:
        user = await use_case.execute(
            user_id=user_id,
            name=request.name,
            avatar_url=request.avatar_url,
        )
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from None
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
