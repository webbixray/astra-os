from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import TextClause, text

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Result
    from sqlalchemy.ext.asyncio import AsyncSession


class GraphStore:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._batch_queue: list[tuple[TextClause, dict]] = []
        self._batch_size = 0

    async def _execute(self, query: TextClause, params: dict) -> Result:
        return await self.db.execute(query, params)

    async def _flush(self) -> None:
        if not self._batch_queue:
            return
        for query, params in self._batch_queue:
            await self._execute(query, params)
        self._batch_queue.clear()
        self._batch_size = 0

    def _enqueue(self, query_text: str, params: dict) -> None:
        self._batch_queue.append((text(query_text), params))
        self._batch_size += 1

    async def flush(self) -> None:
        await self._flush()

    async def upsert_node(
        self,
        id: UUID,
        organization_id: UUID,
        type: str,
        name: str,
        description: str,
        properties: dict,
        embedding: list[float] | None = None,
    ) -> None:
        await self._execute(
            text("""
                INSERT INTO knowledge_nodes (id, organization_id, type, name, description, properties, embedding)
                VALUES (:id, :org_id, :type, :name, :description, :properties, :embedding::vector)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    properties = EXCLUDED.properties,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
            """),
            {
                "id": id,
                "org_id": organization_id,
                "type": type,
                "name": name,
                "description": description,
                "properties": properties,
                "embedding": embedding,
            },
        )

    async def search_similar(
        self,
        organization_id: UUID,
        embedding: list[float],
        limit: int = 10,
        type_filter: str | None = None,
    ) -> list[dict]:
        embedding_str = f"[{','.join(str(v) for v in embedding)}]"
        query = """
            SELECT id, type, name, description, properties,
                    1 - (embedding <=> :embedding::vector) AS similarity
            FROM knowledge_nodes
            WHERE organization_id = :org_id
        """
        params = {"org_id": organization_id, "embedding": embedding_str}
        if type_filter:
            query += " AND type = :type_filter"
            params["type_filter"] = type_filter
        query += " ORDER BY embedding <=> :embedding::vector LIMIT :limit"
        params["limit"] = limit
        result = await self._execute(text(query), params)
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "type": r[1],
                "name": r[2],
                "description": r[3],
                "properties": r[4],
                "similarity": float(r[5]),
            }
            for r in rows
        ]

    async def insert_relation(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: str,
    ) -> None:
        self._enqueue(
            """
                INSERT INTO knowledge_relations (source_id, target_id, relation_type)
                VALUES (:source_id, :target_id, :relation_type)
                ON CONFLICT DO NOTHING
            """,
            {
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type,
            },
        )

    async def get_relations(self, node_id: UUID, relation_type: str | None = None) -> list[dict]:
        query = """
            SELECT r.id, r.source_id, r.target_id, r.relation_type,
                   n_source.name AS source_name, n_target.name AS target_name,
                   n_source.type AS source_type, n_target.type AS target_type
            FROM knowledge_relations r
            JOIN knowledge_nodes n_source ON r.source_id = n_source.id
            JOIN knowledge_nodes n_target ON r.target_id = n_target.id
            WHERE r.source_id = :node_id OR r.target_id = :node_id
        """
        params = {"node_id": node_id}
        if relation_type:
            query += " AND r.relation_type = :relation_type"
            params["relation_type"] = relation_type
        result = await self._execute(text(query), params)
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "source_id": str(r[1]),
                "target_id": str(r[2]),
                "relation_type": r[3],
                "source_name": r[4],
                "target_name": r[5],
                "source_type": r[6],
                "target_type": r[7],
            }
            for r in rows
        ]

    async def upsert_memory(
        self,
        id: UUID,
        organization_id: UUID,
        user_id: UUID,
        type: str,
        importance: str,
        key: str,
        value: str,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self._execute(
            text("""
                INSERT INTO memories (id, organization_id, user_id, type, importance, key, value, embedding, metadata)
                VALUES (:id, :org_id, :user_id, :type, :importance, :key, :value, :embedding::vector, :metadata)
                ON CONFLICT (organization_id, user_id, key) DO UPDATE SET
                    value = EXCLUDED.value,
                    type = EXCLUDED.type,
                    importance = EXCLUDED.importance,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """),
            {
                "id": id,
                "org_id": organization_id,
                "user_id": user_id,
                "type": type,
                "importance": importance,
                "key": key,
                "value": value,
                "embedding": embedding,
                "metadata": metadata or {},
            },
        )

    async def get_memories(
        self,
        organization_id: UUID,
        user_id: UUID,
        type: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        query = """
            SELECT id, type, importance, key, value, metadata, created_at
            FROM memories
            WHERE organization_id = :org_id AND user_id = :user_id
        """
        params = {"org_id": organization_id, "user_id": user_id}
        if type:
            query += " AND type = :type"
            params["type"] = type
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await self._execute(text(query), params)
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "type": r[1],
                "importance": r[2],
                "key": r[3],
                "value": r[4],
                "metadata": r[5],
                "created_at": r[6].isoformat() if r[6] else "",
            }
            for r in rows
        ]

    async def search_memories(
        self,
        organization_id: UUID,
        user_id: UUID,
        embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        embedding_str = f"[{','.join(str(v) for v in embedding)}]"
        result = await self._execute(
            text("""
                SELECT id, type, importance, key, value, metadata, created_at,
                        1 - (embedding <=> :embedding::vector) AS similarity
                FROM memories
                WHERE organization_id = :org_id AND user_id = :user_id
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {
                "org_id": organization_id,
                "user_id": user_id,
                "embedding": embedding_str,
                "limit": limit,
            },
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "type": r[1],
                "importance": r[2],
                "key": r[3],
                "value": r[4],
                "metadata": r[5],
                "created_at": r[6].isoformat() if r[6] else "",
                "similarity": float(r[7]),
            }
            for r in rows
        ]
