"""Knowledge Optimization API routes — predictive optimization endpoints.

M4 Intelligence: Provides endpoints for budget optimization,
creative fatigue detection, and audience expansion suggestions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.knowledge.knowledge_service import (
    KnowledgeGraphService,
)
from app.domain.services.knowledge.predictive_optimization import (
    PredictiveOptimizer,
)
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id

router = APIRouter(prefix="/knowledge/optimization", tags=["knowledge-optimization"])


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

async def get_optimizer(db: AsyncSession = Depends(get_db)) -> PredictiveOptimizer:
    gs = GraphStore(db)
    return PredictiveOptimizer(
        knowledge_service=KnowledgeGraphService(gs),
    )


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CampaignData(BaseModel):
    id: str
    name: str
    daily_budget: float = 0
    roas: float = 0
    impressions: float = 0
    clicks: float = 0
    conversions: float = 0
    spend: float = 0


class BudgetOptimizationRequest(BaseModel):
    organization_id: UUID
    campaigns: list[CampaignData] = Field(..., min_length=1)
    total_budget: float | None = None


class CreativeFatigueRequest(BaseModel):
    organization_id: UUID
    creatives: list[dict] = Field(..., min_length=1)


class AudienceExpansionRequest(BaseModel):
    organization_id: UUID
    source_audience: str = Field(..., min_length=1, max_length=500)
    campaign_id: UUID | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SuggestionsRequest(BaseModel):
    organization_id: UUID
    campaigns: list[CampaignData] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/budget")
async def optimize_budget(
    request: BudgetOptimizationRequest,
    optimizer: PredictiveOptimizer = Depends(get_optimizer),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Suggest budget reallocation across campaigns based on performance."""
    allocations = await optimizer.optimize_budget(
        organization_id=request.organization_id,
        campaigns=[c.model_dump() for c in request.campaigns],
        total_budget=request.total_budget,
    )
    return {
        "allocations": [a.to_dict() for a in allocations],
        "total_campaigns": len(allocations),
    }


@router.post("/creative-fatigue")
async def detect_creative_fatigue(
    request: CreativeFatigueRequest,
    optimizer: PredictiveOptimizer = Depends(get_optimizer),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Detect creative fatigue from performance time series."""
    results = await optimizer.detect_creative_fatigue(
        organization_id=request.organization_id,
        creatives=request.creatives,
    )
    fatigued_count = sum(1 for r in results if r.is_fatigued)
    return {
        "results": [r.to_dict() for r in results],
        "total_creatives": len(results),
        "fatigued_count": fatigued_count,
    }


@router.post("/audience-expansion")
async def suggest_audience_expansion(
    request: AudienceExpansionRequest,
    optimizer: PredictiveOptimizer = Depends(get_optimizer),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Suggest audience expansions based on knowledge graph analysis."""
    suggestions = await optimizer.suggest_audience_expansion(
        organization_id=request.organization_id,
        source_audience=request.source_audience,
        campaign_id=request.campaign_id,
        limit=request.limit,
    )
    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "source_audience": request.source_audience,
        "total_suggestions": len(suggestions),
    }


@router.post("/suggestions")
async def generate_suggestions(
    request: SuggestionsRequest,
    optimizer: PredictiveOptimizer = Depends(get_optimizer),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Generate unified optimization suggestions across all dimensions."""
    suggestions = await optimizer.generate_suggestions(
        organization_id=request.organization_id,
        campaign_data=[c.model_dump() for c in request.campaigns],
    )
    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "total": len(suggestions),
    }
