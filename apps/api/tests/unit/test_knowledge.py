from uuid import uuid4

from app.domain.entities.knowledge.memory import (
    ContextMemory,
    Memory,
    MemoryImportance,
    MemoryType,
)
from app.domain.entities.knowledge.node import (
    RELATION_TYPES,
    KnowledgeNode,
    KnowledgeRelation,
    NodeType,
)


class TestMemory:
    def test_create_memory(self):
        org_id = uuid4()
        user_id = uuid4()
        m = Memory.create(
            organization_id=org_id,
            user_id=user_id,
            key="pref_theme",
            value="dark",
            type=MemoryType.PREFERENCE,
            importance=MemoryImportance.HIGH,
        )
        assert m.organization_id == org_id
        assert m.user_id == user_id
        assert m.key == "pref_theme"
        assert m.value == "dark"
        assert m.type == MemoryType.PREFERENCE
        assert m.importance == MemoryImportance.HIGH
        assert m.embedding is None
        assert m.metadata == {}
        assert m.expires_at is None

    def test_defaults(self):
        m = Memory.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            key="k",
            value="v",
        )
        assert m.type == MemoryType.CONVERSATION
        assert m.importance == MemoryImportance.MEDIUM


class TestContextMemory:
    def test_defaults(self):
        cm = ContextMemory()
        assert cm.current_page == ""
        assert cm.active_campaign_id is None
        assert cm.active_content_id is None
        assert cm.recent_queries == []
        assert cm.user_preferences == {}
        assert cm.session_started_at is not None


class TestKnowledgeNode:
    def test_create_node(self):
        org_id = uuid4()
        n = KnowledgeNode.create(
            organization_id=org_id,
            type=NodeType.CAMPAIGN,
            name="Summer Campaign",
            description="Q3 push",
            properties={"budget": 10000},
        )
        assert n.organization_id == org_id
        assert n.type == NodeType.CAMPAIGN
        assert n.name == "Summer Campaign"
        assert n.description == "Q3 push"
        assert n.properties == {"budget": 10000}
        assert n.embedding is None

    def test_defaults(self):
        n = KnowledgeNode.create(organization_id=uuid4(), type=NodeType.CONCEPT, name="X")
        assert n.type == NodeType.CONCEPT
        assert n.description == ""
        assert n.properties == {}


class TestKnowledgeRelation:
    def test_create_relation(self):
        src = uuid4()
        tgt = uuid4()
        r = KnowledgeRelation.create(
            source_id=src,
            target_id=tgt,
            relation_type="part_of",
            weight=0.9,
        )
        assert r.source_id == src
        assert r.target_id == tgt
        assert r.relation_type == "part_of"
        assert r.weight == 0.9
        assert r.properties == {}

    def test_defaults(self):
        r = KnowledgeRelation.create(source_id=uuid4(), target_id=uuid4())
        assert r.relation_type == "related_to"
        assert r.weight == 1.0


class TestNodeTypeEnum:
    def test_all_types_present(self):
        expected = [
            "campaign", "content", "brand", "audience", "topic",
            "channel", "user", "organization", "ad_account",
            "asset", "concept",
        ]
        for e in expected:
            assert hasattr(NodeType, e.upper())


class TestRELATION_TYPES:
    def test_mapping(self):
        assert RELATION_TYPES["belongs_to"] == "BELONGS_TO"
        assert RELATION_TYPES["related_to"] == "RELATED_TO"
        assert RELATION_TYPES["similar_to"] == "SIMILAR_TO"
        assert RELATION_TYPES["part_of"] == "PART_OF"
        assert RELATION_TYPES["created_by"] == "CREATED_BY"
        assert RELATION_TYPES["targets"] == "TARGETS"
        assert RELATION_TYPES["mentions"] == "MENTIONS"
        assert RELATION_TYPES["derived_from"] == "DERIVED_FROM"
        assert RELATION_TYPES["informs"] == "INFORMS"
        assert len(RELATION_TYPES) == 9
