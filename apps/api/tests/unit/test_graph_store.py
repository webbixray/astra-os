from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def store(mock_db):
    return GraphStore(db=mock_db)


class TestUpsertNode:
    @pytest.mark.asyncio
    async def test_upsert_node_calls_execute_and_commit(self, store, mock_db):
        node_id = uuid4()
        org_id = uuid4()
        await store.upsert_node(
            id=node_id,
            organization_id=org_id,
            type="campaign",
            name="Summer Campaign",
            description="Q3 push",
            properties={"budget": 10000},
            embedding=[0.1, 0.2],
        )
        assert mock_db.execute.called
        call_sql = mock_db.execute.call_args[0][0].text
        assert "INSERT INTO knowledge_nodes" in call_sql
        assert "ON CONFLICT (id) DO UPDATE" in call_sql

    @pytest.mark.asyncio
    async def test_upsert_node_without_embedding(self, store, mock_db):
        await store.upsert_node(
            id=uuid4(),
            organization_id=uuid4(),
            type="concept",
            name="Test",
            description="",
            properties={},
        )
        assert mock_db.execute.called


class TestSearchSimilar:
    @pytest.mark.asyncio
    async def test_search_similar_returns_formatted_results(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (uuid4(), "campaign", "Test", "Desc", {"k": "v"}, 0.95),
        ]
        mock_db.execute.return_value = mock_result

        results = await store.search_similar(
            organization_id=uuid4(),
            embedding=[0.1, 0.2, 0.3],
            limit=5,
        )

        assert len(results) == 1
        assert results[0]["type"] == "campaign"
        assert results[0]["name"] == "Test"
        assert results[0]["similarity"] == 0.95
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_search_similar_with_type_filter(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        results = await store.search_similar(
            organization_id=uuid4(),
            embedding=[0.1, 0.2],
            type_filter="campaign",
        )

        assert results == []
        call_sql = mock_db.execute.call_args[0][0].text
        assert "AND type = :type_filter" in call_sql

    @pytest.mark.asyncio
    async def test_search_similar_embeds_vector_in_sql(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await store.search_similar(
            organization_id=uuid4(),
            embedding=[0.1, 0.2, 0.3],
        )

        params = mock_db.execute.call_args[0][1]
        assert params["embedding"] == "[0.1,0.2,0.3]"


class TestInsertRelation:
    @pytest.mark.asyncio
    async def test_insert_relation(self, store, mock_db):
        source_id = uuid4()
        target_id = uuid4()
        await store.insert_relation(source_id, target_id, "belongs_to")
        await store.flush()

        call_sql = mock_db.execute.call_args[0][0].text
        assert "INSERT INTO knowledge_relations" in call_sql
        assert "ON CONFLICT DO NOTHING" in call_sql


class TestGetRelations:
    @pytest.mark.asyncio
    async def test_get_relations_returns_formatted(self, store, mock_db):
        node_id = uuid4()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (uuid4(), uuid4(), node_id, "belongs_to", "Source", "Target", "campaign", "concept"),
        ]
        mock_db.execute.return_value = mock_result

        results = await store.get_relations(node_id)

        assert len(results) == 1
        assert results[0]["relation_type"] == "belongs_to"
        assert results[0]["source_name"] == "Source"
        assert results[0]["target_name"] == "Target"

    @pytest.mark.asyncio
    async def test_get_relations_with_type_filter(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await store.get_relations(node_id=uuid4(), relation_type="belongs_to")

        call_sql = mock_db.execute.call_args[0][0].text
        assert "AND r.relation_type = :relation_type" in call_sql


class TestUpsertMemory:
    @pytest.mark.asyncio
    async def test_upsert_memory_calls_execute_and_commit(self, store, mock_db):
        await store.upsert_memory(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            type="preference",
            importance="high",
            key="theme",
            value="dark",
            embedding=[0.5, 0.6],
            metadata={"source": "user_setting"},
        )
        call_sql = mock_db.execute.call_args[0][0].text
        assert "INSERT INTO memories" in call_sql
        assert "ON CONFLICT (organization_id, user_id, key)" in call_sql

    @pytest.mark.asyncio
    async def test_upsert_memory_default_metadata(self, store, mock_db):
        await store.upsert_memory(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            type="conversation",
            importance="medium",
            key="last_query",
            value="test",
        )
        params = mock_db.execute.call_args[0][1]
        assert params["metadata"] == {}


class TestGetMemories:
    @pytest.mark.asyncio
    async def test_get_memories_returns_formatted(self, store, mock_db):
        now = MagicMock()
        now.isoformat.return_value = "2026-01-01T00:00:00"
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (uuid4(), "preference", "high", "theme", "dark", {"k": "v"}, now),
        ]
        mock_db.execute.return_value = mock_result

        results = await store.get_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
        )

        assert len(results) == 1
        assert results[0]["type"] == "preference"
        assert results[0]["key"] == "theme"
        assert results[0]["value"] == "dark"
        assert results[0]["created_at"] == "2026-01-01T00:00:00"

    @pytest.mark.asyncio
    async def test_get_memories_with_type_filter(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await store.get_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
            type="preference",
        )

        call_sql = mock_db.execute.call_args[0][0].text
        assert "AND type = :type" in call_sql

    @pytest.mark.asyncio
    async def test_get_memories_default_limit(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await store.get_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
        )

        params = mock_db.execute.call_args[0][1]
        assert params["limit"] == 20

    @pytest.mark.asyncio
    async def test_get_memories_handles_none_created_at(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (uuid4(), "type", "importance", "key", "value", {}, None),
        ]
        mock_db.execute.return_value = mock_result

        results = await store.get_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
        )

        assert results[0]["created_at"] == ""


class TestSearchMemories:
    @pytest.mark.asyncio
    async def test_search_memories_returns_formatted(self, store, mock_db):
        now = MagicMock()
        now.isoformat.return_value = "2026-01-01T00:00:00"
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (uuid4(), "preference", "high", "theme", "dark", {"k": "v"}, now, 0.92),
        ]
        mock_db.execute.return_value = mock_result

        results = await store.search_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
            embedding=[0.1, 0.2],
        )

        assert len(results) == 1
        assert results[0]["key"] == "theme"
        assert results[0]["similarity"] == 0.92
        assert results[0]["created_at"] == "2026-01-01T00:00:00"

    @pytest.mark.asyncio
    async def test_search_memories_embeds_vector(self, store, mock_db):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await store.search_memories(
            organization_id=uuid4(),
            user_id=uuid4(),
            embedding=[0.1, 0.2, 0.3],
        )

        params = mock_db.execute.call_args[0][1]
        assert params["embedding"] == "[0.1,0.2,0.3]"
