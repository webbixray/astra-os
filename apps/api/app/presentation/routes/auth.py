"""Authentication routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from uuid import UUID

    from app.infrastructure.db.repositories.user_repository import (
        UserRepositoryImpl,
    )

from app.application.use_cases.auth_use_cases import AuthService
from app.config import config
from app.presentation.dependencies import get_user_repo
from app.presentation.middleware.auth import require_user_id
from app.presentation.schemas.common import MessageResponse, UserResponse

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class SignInRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


def get_auth_service(
    request: Request,
    repo: UserRepositoryImpl = Depends(get_user_repo),
) -> AuthService:
    redis_cache = getattr(request.app.state, "redis", None)
    redis_client = getattr(redis_cache, "client", None)
    return AuthService(repo, redis_client=redis_client)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = config.is_production
    response.set_cookie(
        key="astra_access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=900,
        path="/",
    )
    response.set_cookie(
        key="astra_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=604800,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("astra_access_token", path="/")
    response.delete_cookie("astra_refresh_token", path="/")


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=201,
    summary="Register a new user",
)
async def sign_up(
    request: SignUpRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.sign_up(
        email=request.email,
        password=request.password,
        name=request.name,
    )
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse(**result["user"]),
    )


@router.post("/signin", response_model=AuthResponse, summary="Sign in with credentials")
async def sign_in(
    request: SignInRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.sign_in(
        email=request.email,
        password=request.password,
    )
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse(**result["user"]),
    )


@router.post("/refresh", response_model=AuthResponse, summary="Refresh access token")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    refresh_token = body.refresh_token or request.cookies.get("astra_refresh_token", "")
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="No refresh token provided")
    result = await service.refresh_access_token(refresh_token)
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse(**result["user"]),
    )


@router.post("/logout", response_model=MessageResponse, summary="Log out user")
async def logout(
    request: Request,
    body: RefreshRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    refresh_token = body.refresh_token or request.cookies.get("astra_refresh_token", "")
    if refresh_token:
        await service.logout(refresh_token)
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_current_user(
    user_id: UUID = Depends(require_user_id),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.get_current_user(user_id)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
