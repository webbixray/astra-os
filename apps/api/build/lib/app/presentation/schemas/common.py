from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")
DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: str
    details: dict | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    page: int
    limit: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    checks: dict[str, bool] | None = None
    details: dict[str, str] | None = None
    duration_ms: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan_tier: str
    settings: dict
    created_at: datetime
    updated_at: datetime


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    permissions: list[str]
    joined_at: datetime


class MessageResponse(BaseModel):
    message: str
    success: bool = True
