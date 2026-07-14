"""Knowledge RAG API routes — hybrid search and context assembly endpoints.

M4 Intelligence: Provides endpoints for RAG-based knowledge search
and context assembly for agent prompts.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.knowledge.knowledge_service import (
    KnowledgeGraphService,
)
from app.application.use_cases.knowledge.memory_service import MemoryService
from app.domain.services.knowledge.rag_pipeline import RagPipeline
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id

router = APIRouter(prefix="/knowledge/rag", tags=["knowledge-rag"])


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

async def get_rag_pipeline(db: AsyncSession = Depends(get_db)) -> RagPipeline:
    gs = GraphStore(db)
    return RagPipeline(
        knowledge_service=KnowledgeGraphService(gs),
        memory_service=MemoryService(gs),
    )


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RAGSearchRequest(BaseModel):
    organization_id: UUID
    query: str = Field(..., min_length=1, max_length=2000)
    type_filter: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)


class RAGContextRequest(BaseModel):
    organization_id: UUID
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: UUID | None = None
    agent_id: str | None = None
    max_results: int = Field(default=10, ge=1, le=50)
    include_brand_guidelines: bool = True
    include_memories: bool = True


class IngestBrandGuidelinesRequest(BaseModel):
    organization_id: UUID
    guidelines_text: str = Field(..., min_length=1, max_length=50000)
    name: str = Field(default="Brand Guidelines", max_length=500)
    properties: dict = {}


class IngestCampaignDataRequest(BaseModel):
    organization_id: UUID
    campaign_id: UUID
    campaign_name: str = Field(..., min_length=1, max_length=500)
    data: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/search")
async def rag_search(
    request: RAGSearchRequest,
    pipeline: RagPipeline = Depends(get_rag_pipeline),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Hybrid search combining vector similarity, keyword matching,
    and knowledge graph traversal.
    """
    results = await pipeline.search(
        query=request.query,
        organization_id=request.organization_id,
        type_filter=request.type_filter,
        limit=request.limit,
        min_score=request.min_score,
    )
    return {
        "results": [r.to_dict() if hasattr(r, "to_dict") else {
            "node_id": r.node_id,
            "node_type": r.node_type,
            "name": r.name,
            "description": r.description,
            "score": round(r.score, 3),
            "source": r.source,
            "relevance": r.relevance_label,
            "properties": r.properties,
            "related_node_ids": r.related_node_ids,
        } for r in results],
        "total": len(results),
        "query": request.query,
    }


@router.post("/context")
async def assemble_context(
    request: RAGContextRequest,
    pipeline: RagPipeline = Depends(get_rag_pipeline),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Assemble rich context for an agent prompt, including knowledge
    graph results, memories, and brand guidelines.
    """
    ctx = await pipeline.assemble_context(
        query=request.query,
        organization_id=request.organization_id,
        user_id=request.user_id or user_id,
        agent_id=request.agent_id,
        max_results=request.max_results,
        include_brand_guidelines=request.include_brand_guidelines,
        include_memories=request.include_memories,
    )
    return {
        "query": ctx.query,
        "context_text": ctx.context_text,
        "result_count": ctx.result_count,
        "high_relevance_count": ctx.high_relevance_count,
        "source_node_ids": ctx.source_node_ids,
        "brand_guidelines": ctx.brand_guidelines,
        "memory_context_count": len(ctx.memory_context),
        "assembled_at": ctx.assembled_at,
    }


@router.post("/ingest/brand-guidelines")
async def ingest_brand_guidelines(
    request: IngestBrandGuidelinesRequest,
    pipeline: RagPipeline = Depends(get_rag_pipeline),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Ingest brand guidelines into the knowledge graph."""
    result = await pipeline.ingest_brand_guidelines(
        organization_id=request.organization_id,
        guidelines_text=request.guidelines_text,
        name=request.name,
        properties=request.properties,
        user_id=user_id,
    )
    return result.to_dict()


@router.post("/ingest/campaign-data")
async def ingest_campaign_data(
    request: IngestCampaignDataRequest,
    pipeline: RagPipeline = Depends(get_rag_pipeline),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Ingest campaign metrics and insights into the knowledge graph."""
    result = await pipeline.ingest_campaign_data(
        organization_id=request.organization_id,
        campaign_id=request.campaign_id,
        campaign_name=request.campaign_name,
        data=request.data,
        user_id=user_id,
    )
    return result.to_dict()
