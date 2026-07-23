from uuid import UUID

from app.domain.entities.knowledge.node import KnowledgeNode, NodeType
from app.infrastructure.external_adapters.knowledge.embedding_service import (
    get_embedding_provider,
)
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore


class KnowledgeGraphService:
    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
        self.embedder = get_embedding_provider()

    async def create_node(
        self,
        organization_id: UUID,
        type: NodeType,
        name: str,
        description: str = "",
        properties: dict | None = None,
    ) -> dict:
        node = KnowledgeNode.create(
            organization_id=organization_id,
            type=type,
            name=name,
            description=description,
            properties=properties or {},
        )

        embedding_text = f"{name}: {description}"
        embedding = await self.embedder.embed(embedding_text)

        await self.graph_store.upsert_node(
            id=node.id,
            organization_id=organization_id,
            type=type.value,
            name=name,
            description=description,
            properties=properties or {},
            embedding=embedding,
        )

        return {
            "id": str(node.id),
            "type": type.value,
            "name": name,
            "description": description,
        }

    async def search(
        self,
        organization_id: UUID,
        query: str,
        type_filter: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        embedding = await self.embedder.embed(query)
        return await self.graph_store.search_similar(
            organization_id=organization_id,
            embedding=embedding,
            limit=limit,
            type_filter=type_filter,
        )

    async def create_relation(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: str = "related_to",
    ) -> dict:
        await self.graph_store.insert_relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
        )
        return {
            "source_id": str(source_id),
            "target_id": str(target_id),
            "relation_type": relation_type,
        }

    async def get_node_relations(
        self, node_id: UUID, relation_type: str | None = None
    ) -> list[dict]:
        return await self.graph_store.get_relations(
            node_id=node_id,
            relation_type=relation_type,
        )

    async def index_campaign(
        self, organization_id: UUID, campaign_id: UUID, name: str, description: str
    ) -> None:
        await self.create_node(
            organization_id=organization_id,
            type=NodeType.CAMPAIGN,
            name=name,
            description=description,
            properties={"campaign_id": str(campaign_id)},
        )

    async def index_content(
        self, organization_id: UUID, content_id: UUID, title: str, body: str
    ) -> None:
        await self.create_node(
            organization_id=organization_id,
            type=NodeType.CONTENT,
            name=title,
            description=body[:500],
            properties={"content_id": str(content_id)},
        )
