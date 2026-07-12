"""Design Partner API Routes — E6.1 Beta Launch.

Endpoints for managing enterprise design partners, feedback, and support.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.design_partner import (
    DesignPartner,
    DesignPartnerFeedback,
    DesignPartnerStatus,
    DesignPartnerTier,
    FeedbackPriority,
    FeedbackType,
    SupportTicket,
    SupportTicketStatus,
)
from app.domain.services.design_partner_service import DesignPartnerService
from app.infrastructure.db.session import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter(prefix="/design-partners", tags=["design-partners"])


# --- Request/Response Models ---

class CreatePartnerRequest(BaseModel):
    organization_id: UUID
    tier: DesignPartnerTier = DesignPartnerTier.DESIGN_PARTNER
    dedicated_csm_id: UUID | None = None
    contract_expires_at: datetime | None = None
    custom_terms: dict[str, Any] | None = None
    support_tier: str = "priority"
    notes: str = ""
    tags: list[str] = []


class ApprovePartnerRequest(BaseModel):
    contract_signed_at: datetime | None = None


class StartOnboardingRequest(BaseModel):
    csm_id: UUID


class AddMilestoneRequest(BaseModel):
    milestone: str


class UpdatePartnerRequest(BaseModel):
    tier: DesignPartnerTier | None = None
    dedicated_csm_id: UUID | None = None
    contract_expires_at: datetime | None = None
    custom_terms: dict[str, Any] | None = None
    support_tier: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    status: DesignPartnerStatus | None = None


class EngagementUpdateRequest(BaseModel):
    wau: int = 0
    campaigns: int = 0
    ai_interactions: int = 0


class NPSUpdateRequest(BaseModel):
    score: int = Field(ge=0, le=10)


class FeedbackCreateRequest(BaseModel):
    type: FeedbackType
    title: str
    description: str
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    feature_area: str | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    nps_score: int | None = None
    nps_reason: str | None = None
    tags: list[str] = []


class FeedbackUpdateRequest(BaseModel):
    status: str | None = None
    priority: FeedbackPriority | None = None
    assigned_to: UUID | None = None
    resolution_notes: str = ""


class TicketCreateRequest(BaseModel):
    subject: str
    description: str
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    channel: str = "email"
    sla_tier: str = "standard"


class TicketUpdateRequest(BaseModel):
    status: SupportTicketStatus | None = None
    assigned_csm_id: UUID | None = None
    resolution_summary: str = ""
    satisfaction: int | None = None


# --- Dependencies ---

async def get_partner_service(db: AsyncSession = Depends(get_db)) -> DesignPartnerService:
    from app.infrastructure.db.repositories.design_partner_repository import (
        DesignPartnerRepositoryImpl,
        DesignPartnerFeedbackRepositoryImpl,
    )
    repo = DesignPartnerRepositoryImpl(db)
    feedback_repo = DesignPartnerFeedbackRepositoryImpl(db)
    return DesignPartnerService(repo, feedback_repo)


def _require_admin(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Require admin role for design partner management."""
    # In real implementation, check user role
    return user_id


# --- Partner Routes ---

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new design partner",
)
async def create_design_partner(
    request: CreatePartnerRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.create_partner(
        organization_id=request.organization_id,
        tier=request.tier,
        dedicated_csm_id=request.dedicated_csm_id,
        contract_expires_at=request.contract_expires_at,
        custom_terms=request.custom_terms,
        support_tier=request.support_tier,
        notes=request.notes,
        tags=request.tags,
    )
    return partner.to_dict()


@router.get(
    "",
    response_model=list[dict],
    summary="List all design partners",
)
async def list_design_partners(
    status: DesignPartnerStatus | None = Query(None),
    tier: DesignPartnerTier | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> list[dict]:
    partners = await service.list_partners(status=status, tier=tier, limit=limit, offset=offset)
    return [p.to_dict() for p in partners]


@router.get(
    "/stats",
    response_model=dict,
    summary="Get design partner program overview",
)
async def get_program_stats(
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    return await service.get_program_overview()


@router.get(
    "/{partner_id}",
    response_model=dict,
    summary="Get a specific design partner",
)
async def get_design_partner(
    partner_id: UUID,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.get_partner(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Design partner not found")
    return partner.to_dict()


@router.get(
    "/org/{org_id}",
    response_model=dict,
    summary="Get design partner by organization ID",
)
async def get_partner_by_org(
    org_id: UUID,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.get_partner_by_org(org_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Design partner not found for organization")
    return partner.to_dict()


@router.patch(
    "/{partner_id}",
    response_model=dict,
    summary="Update a design partner",
)
async def update_design_partner(
    partner_id: UUID,
    request: UpdatePartnerRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    updates = request.model_dump(exclude_unset=True)
    partner = await service.update_partner(partner_id, updates)
    return partner.to_dict()


@router.post(
    "/{partner_id}/approve",
    response_model=dict,
    summary="Approve a design partner",
)
async def approve_partner(
    partner_id: UUID,
    request: ApprovePartnerRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.approve_partner(partner_id, user_id, request.contract_signed_at)
    return partner.to_dict()


@router.post(
    "/{partner_id}/onboarding/start",
    response_model=dict,
    summary="Start onboarding for a design partner",
)
async def start_onboarding(
    partner_id: UUID,
    request: StartOnboardingRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.start_onboarding(partner_id, request.csm_id)
    return partner.to_dict()


@router.post(
    "/{partner_id}/onboarding/complete",
    response_model=dict,
    summary="Complete onboarding for a design partner",
)
async def complete_onboarding(
    partner_id: UUID,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.complete_onboarding(partner_id)
    return partner.to_dict()


@router.post(
    "/{partner_id}/onboarding/milestone",
    response_model=dict,
    summary="Add an onboarding milestone",
)
async def add_milestone(
    partner_id: UUID,
    request: AddMilestoneRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.add_milestone(partner_id, request.milestone)
    return partner.to_dict()


@router.post(
    "/{partner_id}/engagement",
    response_model=dict,
    summary="Update engagement metrics",
)
async def update_engagement(
    partner_id: UUID,
    request: EngagementUpdateRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.record_engagement(
        partner_id,
        wau=request.wau,
        campaigns=request.campaigns,
        ai_interactions=request.ai_interactions,
    )
    return partner.to_dict()


@router.post(
    "/{partner_id}/nps",
    response_model=dict,
    summary="Update NPS score",
)
async def update_nps(
    partner_id: UUID,
    request: NPSUpdateRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    partner = await service.update_nps(partner_id, request.score)
    return partner.to_dict()


@router.get(
    "/{partner_id}/stats",
    response_model=dict,
    summary="Get comprehensive stats for a design partner",
)
async def get_partner_stats(
    partner_id: UUID,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    return await service.get_partner_stats(partner_id)


# --- Feedback Routes ---

@router.post(
    "/{partner_id}/feedback",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback from a design partner",
)
async def submit_feedback(
    partner_id: UUID,
    request: FeedbackCreateRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Get organization from partner
    partner = await service.get_partner(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Design partner not found")

    feedback = await service.submit_feedback(
        partner_id=partner_id,
        organization_id=partner.organization_id,
        user_id=user_id,
        feedback_type=request.type,
        title=request.title,
        description=request.description,
        priority=request.priority,
        feature_area=request.feature_area,
        related_entity_type=request.related_entity_type,
        related_entity_id=request.related_entity_id,
        nps_score=request.nps_score,
        nps_reason=request.nps_reason,
        tags=request.tags,
    )
    return feedback.to_dict()


@router.get(
    "/{partner_id}/feedback",
    response_model=list[dict],
    summary="List feedback for a design partner",
)
async def list_feedback(
    partner_id: UUID,
    status: str | None = Query(None),
    type: FeedbackType | None = Query(None),
    limit: int = Query(50, le=100),
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> list[dict]:
    feedback = await service.list_feedback(partner_id, status=status, type=type, limit=limit)
    return [f.to_dict() for f in feedback]


@router.patch(
    "/feedback/{feedback_id}",
    response_model=dict,
    summary="Update feedback status/priority",
)
async def update_feedback(
    feedback_id: UUID,
    request: FeedbackUpdateRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    updates = request.model_dump(exclude_unset=True)
    # In a real implementation, this would call a dedicated update method
    # For now, we'll use the triage/resolve methods
    if "status" in updates:
        if updates["status"] == "resolved":
            feedback = await service.resolve_feedback(feedback_id, updates.get("resolution_notes", ""))
        elif updates["status"] == "triaged":
            feedback = await service.triage_feedback(feedback_id, user_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported status transition")
    else:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    return feedback.to_dict()


# --- Support Ticket Routes ---

@router.post(
    "/{partner_id}/tickets",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a support ticket",
)
async def create_ticket(
    partner_id: UUID,
    request: TicketCreateRequest,
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    partner = await service.get_partner(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Design partner not found")

    # In a real implementation, this would use the ticket repository
    raise HTTPException(status_code=501, detail="Ticket creation not fully implemented")


@router.get(
    "/{partner_id}/tickets",
    response_model=list[dict],
    summary="List support tickets for a design partner",
)
async def list_tickets(
    partner_id: UUID,
    status: SupportTicketStatus | None = Query(None),
    limit: int = Query(50, le=100),
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> list[dict]:
    # In a real implementation, this would use the ticket repository
    raise HTTPException(status_code=501, detail="Ticket listing not fully implemented")


# --- Admin Routes ---

@router.get(
    "/admin/overview",
    response_model=dict,
    summary="Get design partner program overview (admin)",
)
async def admin_overview(
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> dict:
    return await service.get_program_overview()


@router.get(
    "/admin/feedback",
    response_model=list[dict],
    summary="List all feedback across all partners (admin)",
)
async def admin_list_all_feedback(
    status: str | None = Query(None),
    type: FeedbackType | None = Query(None),
    priority: FeedbackPriority | None = Query(None),
    limit: int = Query(50, le=100),
    service: DesignPartnerService = Depends(get_partner_service),
    user_id: UUID = Depends(_require_admin),
) -> list[dict]:
    feedback = await service.list_all_feedback(status=status, type=type, priority=priority, limit=limit)
    return [f.to_dict() for f in feedback]