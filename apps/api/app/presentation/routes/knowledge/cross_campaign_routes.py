"""Knowledge Cross-Campaign API routes — pattern mining and transfer learning endpoints.

M4 Intelligence: Provides endpoints for discovering patterns across campaigns
and recommending transfer strategies.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.knowledge.knowledge_service import (
    KnowledgeGraphService,
)
from app.domain.services.knowledge.cross_campaign_learning import (
    CrossCampaignLearner,
    PatternType,
)
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id

router = APIRouter(prefix="/knowledge/patterns", tags=["knowledge-patterns"])


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

async def get_learner(db: AsyncSession = Depends(get_db)) -> CrossCampaignLearner:
    gs = GraphStore(db)
    return CrossCampaignLearner(
        knowledge_service=KnowledgeGraphService(gs),
    )


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class MinePatternsRequest(BaseModel):
    organization_id: UUID
    campaign_ids: list[str] | None = None
    pattern_types: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=50)


class TransferSuggestionsRequest(BaseModel):
    organization_id: UUID
    target_campaign_id: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class LearningInsightsRequest(BaseModel):
    organization_id: UUID
    limit: int = Field(default=10, ge=1, le=50)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/mine")
async def mine_patterns(
    request: MinePatternsRequest,
    learner: CrossCampaignLearner = Depends(get_learner),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Mine patterns across campaigns from the knowledge graph."""
    # Convert string pattern types to enum
    pattern_types = None
    if request.pattern_types:
        pattern_types = []
        for pt in request.pattern_types:
            try:
                pattern_types.append(PatternType(pt))
            except ValueError:
                continue  # skip invalid types

    patterns = await learner.mine_patterns(
        organization_id=request.organization_id,
        campaign_ids=request.campaign_ids,
        pattern_types=pattern_types,
        limit=request.limit,
    )
    return {
        "patterns": [p.to_dict() for p in patterns],
        "total": len(patterns),
    }


@router.post("/transfer")
async def suggest_transfers(
    request: TransferSuggestionsRequest,
    learner: CrossCampaignLearner = Depends(get_learner),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Suggest transferring patterns from high-performing campaigns
    to a target campaign.
    """
    recommendations = await learner.suggest_transfers(
        organization_id=request.organization_id,
        target_campaign_id=request.target_campaign_id,
        limit=request.limit,
    )
    return {
        "recommendations": [r.to_dict() for r in recommendations],
        "target_campaign_id": request.target_campaign_id,
        "total": len(recommendations),
    }


@router.post("/insights")
async def get_learning_insights(
    request: LearningInsightsRequest,
    learner: CrossCampaignLearner = Depends(get_learner),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Get aggregated learning insights from cross-campaign analysis."""
    insights = await learner.get_learning_insights(
        organization_id=request.organization_id,
        limit=request.limit,
    )
    return {
        "insights": [i.to_dict() for i in insights],
        "total": len(insights),
    }
