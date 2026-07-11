from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

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

logger = logging.getLogger(__name__)

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


def get_auth_service(repo: UserRepositoryImpl = Depends(get_user_repo)) -> AuthService:
    return AuthService(repo)


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
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("astra_access_token", path="/")
    response.delete_cookie("astra_refresh_token", path="/api/v1/auth")


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def sign_up(
    request: SignUpRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        result = await service.sign_up(
            email=request.email,
            password=request.password,
            name=request.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected error during sign up")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed"
        ) from None
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
    try:
        result = await service.sign_in(
            email=request.email,
            password=request.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected error during sign in")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sign in failed"
        ) from None
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse(**result["user"]),
    )


@router.post("/refresh", response_model=AuthResponse, summary="Refresh access token")
async def refresh_token(
    request: RefreshRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        result = await service.refresh_access_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected error during token refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed"
        ) from None
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse(**result["user"]),
    )


@router.post("/logout", response_model=MessageResponse, summary="Log out user")
async def logout(
    request: RefreshRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await service.logout(request.refresh_token)
    except Exception:
        logger.exception("Unexpected error during logout")
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_current_user(
    user_id: UUID = Depends(require_user_id),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        user = await service.get_current_user(user_id)
    except Exception:
        logger.exception("Unexpected error fetching current user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch user profile"
        ) from None
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
