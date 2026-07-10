from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.presentation.schemas.common import SuccessResponse


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    status: str
    budget_amount: float | None = None
    budget_currency: str = "USD"
    start_date: str | None = None
    end_date: str | None = None
    channels: list[str] = []
    objective: str | None = None
    created_by: UUID
    ai_generated: bool = False
    created_at: datetime
    updated_at: datetime


class ContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID | None = None
    organization_id: UUID
    title: str
    content_type: str
    body: str = ""
    status: str = "draft"
    brand_profile_id: UUID | None = None
    generated_by_ai: bool = False
    version: int = 1
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class CampaignResponseEnvelope(SuccessResponse[CampaignResponse]):
    pass


class ContentResponseEnvelope(SuccessResponse[ContentResponse]):
    pass
