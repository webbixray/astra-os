from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.knowledge.knowledge_service import KnowledgeGraphService
from app.application.use_cases.knowledge.memory_service import MemoryService
from app.domain.entities.knowledge.node import NodeType
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateNodeRequest(BaseModel):
    organization_id: UUID
    type: str
    name: str
    description: str = ""
    properties: dict = {}


class CreateRelationRequest(BaseModel):
    organization_id: UUID
    source_id: UUID
    target_id: UUID
    relation_type: str = "related_to"


class RememberRequest(BaseModel):
    organization_id: UUID
    user_id: UUID
    key: str
    value: str
    type: str = "conversation"
    importance: str = "medium"


class RecallRequest(BaseModel):
    organization_id: UUID
    user_id: UUID
    query: str
    limit: int = 5


class SearchRequest(BaseModel):
    organization_id: UUID
    query: str
    type_filter: str | None = None
    limit: int = 10


async def get_graph_store(db: AsyncSession = Depends(get_db)) -> GraphStore:
    return GraphStore(db)


@router.post("/knowledge/nodes")
async def create_node(
    request: CreateNodeRequest,
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = KnowledgeGraphService(graph_store)
    return await service.create_node(
        organization_id=request.organization_id,
        type=NodeType(request.type),
        name=request.name,
        description=request.description,
        properties=request.properties,
    )


@router.post("/knowledge/search")
async def search_knowledge(
    request: SearchRequest,
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = KnowledgeGraphService(graph_store)
    return await service.search(
        organization_id=request.organization_id,
        query=request.query,
        type_filter=request.type_filter,
        limit=request.limit,
    )


@router.post("/knowledge/relations")
async def create_relation(
    request: CreateRelationRequest,
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = KnowledgeGraphService(graph_store)
    return await service.create_relation(
        source_id=request.source_id,
        target_id=request.target_id,
        relation_type=request.relation_type,
    )


@router.get("/knowledge/nodes/{node_id}/relations")
async def get_node_relations(
    node_id: UUID,
    relation_type: str | None = Query(None),
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = KnowledgeGraphService(graph_store)
    node = await service.get_node(node_id)
    if node:
        await require_org_role(node.organization_id, "viewer", user_id, db)
    return await service.get_node_relations(
        node_id=node_id,
        relation_type=relation_type,
    )


@router.post("/knowledge/memory/remember")
async def remember(
    request: RememberRequest,
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    from app.domain.entities.knowledge.memory import MemoryImportance, MemoryType
    service = MemoryService(graph_store)
    return await service.remember(
        organization_id=request.organization_id,
        user_id=request.user_id,
        key=request.key,
        value=request.value,
        type=MemoryType(request.type),
        importance=MemoryImportance(request.importance),
    )


@router.post("/knowledge/memory/recall")
async def recall(
    request: RecallRequest,
    graph_store: GraphStore = Depends(get_graph_store),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(request.organization_id, "viewer", user_id, db)
    service = MemoryService(graph_store)
    return await service.recall(
        organization_id=request.organization_id,
        user_id=request.user_id,
        query=request.query,
        limit=request.limit,
    )


@router.get("/knowledge/memory/{organization_id}/{user_id}")
async def get_memories(
    organization_id: UUID,
    user_id: UUID,
    type: str | None = Query(None),
    graph_store: GraphStore = Depends(get_graph_store),
    current_user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", current_user_id, db)
    service = MemoryService(graph_store)
    return await service.get_memories(
        organization_id=organization_id,
        user_id=user_id,
        type=type,
    )
