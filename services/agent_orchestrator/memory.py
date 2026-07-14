"""Memory Manager for agent memory systems."""

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""

    memory_id: UUID = field(default_factory=uuid4)
    agent_id: UUID | None = None
    tenant_id: UUID | None = None
    memory_type: str = "working"  # working, episodic, semantic
    key: str = ""
    value: Any = None
    embedding: list[float] | None = None
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None


class MemoryManager:
    """Unified memory manager for working, episodic, and semantic memory."""

    def __init__(
        self,
        pg_pool: asyncpg.Pool | None = None,
        redis_client: redis.Redis | None = None,
        embedding_dim: int = 1536,
    ):
        self.pg_pool = pg_pool
        self.redis = redis_client
        self.embedding_dim = embedding_dim

        self._working_ttl = 3600  # 1 hour
        self._episodic_ttl = 86400 * 30  # 30 days
        self._semantic_ttl = 86400 * 365  # 1 year

    async def store(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        memory_type: str,
        key: str,
        value: Any,
        importance: float = 0.5,
        tags: list[str] | None = None,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> MemoryEntry:
        """Store a memory entry."""
        memory = MemoryEntry(
            agent_id=agent_id,
            tenant_id=tenant_id,
            memory_type=memory_type,
            key=key,
            value=value,
            embedding=embedding,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
        )

        if ttl_seconds:
            memory.expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        elif memory_type == "working":
            memory.expires_at = datetime.now(UTC) + timedelta(seconds=self._working_ttl)
        elif memory_type == "episodic":
            memory.expires_at = datetime.now(UTC) + timedelta(seconds=self._episodic_ttl)
        elif memory_type == "semantic":
            memory.expires_at = datetime.now(UTC) + timedelta(seconds=self._semantic_ttl)

        if self.pg_pool:
            await self._store_pg(memory)

        if self.redis and memory_type == "working":
            await self._store_redis(memory)

        return memory

    async def _store_pg(self, memory: MemoryEntry) -> None:
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_memories (
                    memory_id, agent_id, tenant_id, memory_type, key, value,
                    embedding, importance, tags, metadata, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (memory_id) DO UPDATE SET
                    value = EXCLUDED.value,
                    embedding = EXCLUDED.embedding,
                    importance = EXCLUDED.importance,
                    tags = EXCLUDED.tags,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW(),
                    expires_at = EXCLUDED.expires_at
                """,
                memory.memory_id,
                memory.agent_id,
                memory.tenant_id,
                memory.memory_type,
                memory.key,
                json.dumps(memory.value) if not isinstance(memory.value, str) else memory.value,
                memory.embedding,
                memory.importance,
                memory.tags,
                json.dumps(memory.metadata),
                memory.expires_at,
            )

    async def _store_redis(self, memory: MemoryEntry) -> None:
        key = f"memory:{memory.tenant_id}:{memory.agent_id}:{memory.memory_type}:{memory.key}"
        data = {
            "value": json.dumps(memory.value) if not isinstance(memory.value, str) else memory.value,
            "embedding": json.dumps(memory.embedding) if memory.embedding else None,
            "importance": str(memory.importance),
            "tags": json.dumps(memory.tags),
            "metadata": json.dumps(memory.metadata),
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "access_count": "0",
        }

        pipe = self.redis.pipeline()
        pipe.hset(key, mapping={k: v for k, v in data.items() if v is not None})
        if memory.expires_at:
            ttl = int((memory.expires_at - datetime.now(UTC)).total_seconds())
            if ttl > 0:
                pipe.expire(key, ttl)
        else:
            pipe.expire(key, self._working_ttl)
        await pipe.execute()

    async def retrieve(
        self,
        agent_id: UUID | None = None,
        tenant_id: UUID | None = None,
        memory_type: str | None = None,
        key: str | None = None,
        query_embedding: list[float] | None = None,
        query_text: str | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """Retrieve memories with various filters."""
        memories = []

        if key and agent_id and tenant_id and memory_type:
            # Direct key lookup
            if memory_type == "working" and self.redis:
                memory = await self._retrieve_redis(tenant_id, agent_id, memory_type, key)
                if memory:
                    memories.append(memory)

            if not memories and self.pg_pool:
                memory = await self._retrieve_pg_by_key(tenant_id, agent_id, memory_type, key)
                if memory:
                    memories.append(memory)

        elif self.pg_pool:
            # Query-based retrieval
            memories = await self._query_pg(
                agent_id=agent_id,
                tenant_id=tenant_id,
                memory_type=memory_type,
                query_embedding=query_embedding,
                limit=limit,
                min_importance=min_importance,
            )

        # Update access counts
        if memories and self.pg_pool:
            memory_ids = [m.memory_id for m in memories]
            await self._update_access_counts(memory_ids)

        return memories

    async def _retrieve_redis(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        memory_type: str,
        key: str,
    ) -> MemoryEntry | None:
        k = f"memory:{tenant_id}:{agent_id}:{memory_type}:{key}"
        data = await self.redis.hgetall(k)
        if not data:
            return None

        return MemoryEntry(
            memory_id=UUID(data.get(b"memory_id", b"").decode()),
            agent_id=UUID(data.get(b"agent_id", b"").decode()),
            tenant_id=UUID(data.get(b"tenant_id", b"").decode()),
            memory_type=data.get(b"memory_type", b"").decode(),
            key=data.get(b"key", b"").decode(),
            value=json.loads(data.get(b"value", b"{}")),
            embedding=json.loads(data.get(b"embedding", b"[]")) if data.get(b"embedding") else None,
            importance=float(data.get(b"importance", b"0.5")),
            tags=json.loads(data.get(b"tags", b"[]")),
            metadata=json.loads(data.get(b"metadata", b"{}")),
            created_at=datetime.fromisoformat(data.get(b"created_at", b"").decode()),
            updated_at=datetime.fromisoformat(data.get(b"updated_at", b"").decode()),
            access_count=int(data.get(b"access_count", b"0")),
            expires_at=datetime.fromisoformat(data.get(b"expires_at", b"").decode()) if data.get(b"expires_at") else None,
        )

    async def _retrieve_pg_by_key(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        memory_type: str,
        key: str,
    ) -> MemoryEntry | None:
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM agent_memories
                WHERE tenant_id = $1 AND agent_id = $2 AND memory_type = $3 AND key = $4
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                tenant_id, agent_id, memory_type, key,
            )
            if row:
                return self._row_to_memory(row)
        return None

    async def _query_pg(
        self,
        agent_id: UUID | None = None,
        tenant_id: UUID | None = None,
        memory_type: str | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        async with self.pg_pool.acquire() as conn:
            conditions = ["expires_at IS NULL OR expires_at > NOW()", "importance >= $1"]
            params: list[Any] = [min_importance]
            param_idx = 2

            if agent_id:
                conditions.append(f"agent_id = ${param_idx}")
                params.append(agent_id)
                param_idx += 1

            if tenant_id:
                conditions.append(f"tenant_id = ${param_idx}")
                params.append(tenant_id)
                param_idx += 1

            if memory_type:
                conditions.append(f"memory_type = ${param_idx}")
                params.append(memory_type)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            if query_embedding:
                # Vector similarity search
                rows = await conn.fetch(
                    f"""
                    SELECT *, 1 - (embedding <=> $1) AS similarity
                    FROM agent_memories
                    WHERE {where_clause} AND embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT ${param_idx}
                    """,
                    query_embedding,
                    limit,
                    *params,
                )
            else:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM agent_memories
                    WHERE {where_clause}
                    ORDER BY importance DESC, created_at DESC
                    LIMIT ${param_idx}
                    """,
                    limit,
                    *params,
                )

            return [self._row_to_memory(row) for row in rows]

    async def _update_access_counts(self, memory_ids: list[UUID]) -> None:
        if not memory_ids:
            return
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agent_memories
                SET access_count = access_count + 1, last_accessed = NOW()
                WHERE memory_id = ANY($1)
                """,
                memory_ids,
            )

    def _row_to_memory(self, row: asyncpg.Record) -> MemoryEntry:
        return MemoryEntry(
            memory_id=row["memory_id"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            memory_type=row["memory_type"],
            key=row["key"],
            value=json.loads(row["value"]) if isinstance(row["value"], str) else row["value"],
            embedding=row["embedding"],
            importance=row["importance"],
            tags=row["tags"] or [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row["expires_at"],
            access_count=row["access_count"],
            last_accessed=row["last_accessed"],
        )

    async def forget(
        self,
        agent_id: UUID | None = None,
        tenant_id: UUID | None = None,
        memory_type: str | None = None,
        key: str | None = None,
        memory_id: UUID | None = None,
    ) -> int:
        """Delete memories matching criteria."""
        count = 0

        if memory_id and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM agent_memories WHERE memory_id = $1",
                    memory_id,
                )
                count = int(result.split()[-1]) if result.startswith("DELETE") else 0

        if key and agent_id and tenant_id and memory_type:
            if self.redis and memory_type == "working":
                k = f"memory:{tenant_id}:{agent_id}:{memory_type}:{key}"
                result = await self.redis.delete(k)
                count += result

            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    result = await conn.execute(
                        """
                        DELETE FROM agent_memories
                        WHERE tenant_id = $1 AND agent_id = $2 AND memory_type = $3 AND key = $4
                        """,
                        tenant_id, agent_id, memory_type, key,
                    )
                    count += int(result.split()[-1]) if result.startswith("DELETE") else 0

        return count

    async def consolidate(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        from_type: str = "working",
        to_type: str = "semantic",
        importance_threshold: float = 0.7,
    ) -> int:
        """Consolidate memories from one type to another."""
        memories = await self.retrieve(
            agent_id=agent_id,
            tenant_id=tenant_id,
            memory_type=from_type,
            min_importance=importance_threshold,
            limit=100,
        )

        consolidated = 0
        for memory in memories:
            if memory.importance >= importance_threshold:
                await self.store(
                    agent_id=agent_id,
                    tenant_id=tenant_id,
                    memory_type=to_type,
                    key=memory.key,
                    value=memory.value,
                    importance=memory.importance,
                    tags=memory.tags + ["consolidated"],
                    embedding=memory.embedding,
                    metadata={**memory.metadata, "consolidated_from": from_type},
                )
                await self.forget(memory_id=memory.memory_id)
                consolidated += 1

        return consolidated

    async def get_stats(self, agent_id: UUID | None = None, tenant_id: UUID | None = None) -> dict[str, Any]:
        """Get memory statistics."""
        stats = {"working": 0, "episodic": 0, "semantic": 0, "total_size_mb": 0}

        if self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                conditions = []
                params = []

                if agent_id:
                    conditions.append("agent_id = $1")
                    params.append(agent_id)
                if tenant_id:
                    param_num = len(params) + 1
                    conditions.append(f"tenant_id = ${param_num}")
                    params.append(tenant_id)

                where = "WHERE " + " AND ".join(conditions) if conditions else ""

                rows = await conn.fetch(
                    f"""
                    SELECT
                        memory_type,
                        COUNT(*) as count,
                        COALESCE(SUM(pg_column_size(value)), 0) as size_bytes
                    FROM agent_memories
                    {where}
                    GROUP BY memory_type
                    """,
                    *params,
                )

                for row in rows:
                    stats[row["memory_type"]] = row["count"]
                    stats["total_size_mb"] += row["size_bytes"] / (1024 * 1024)

        return stats
