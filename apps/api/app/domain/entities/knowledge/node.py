from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class NodeType(str, Enum):
    CAMPAIGN = "campaign"
    CONTENT = "content"
    BRAND = "brand"
    AUDIENCE = "audience"
    TOPIC = "topic"
    CHANNEL = "channel"
    USER = "user"
    ORGANIZATION = "organization"
    AD_ACCOUNT = "ad_account"
    ASSET = "asset"
    CONCEPT = "concept"


@dataclass
class KnowledgeNode:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    type: NodeType = NodeType.CONCEPT
    name: str = ""
    description: str = ""
    properties: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        type: NodeType,
        name: str,
        description: str = "",
        properties: dict | None = None,
    ) -> "KnowledgeNode":
        return cls(
            organization_id=organization_id,
            type=type,
            name=name,
            description=description,
            properties=properties or {},
        )


@dataclass
class KnowledgeRelation:
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    relation_type: str = "related_to"
    weight: float = 1.0
    properties: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        source_id: UUID,
        target_id: UUID,
        relation_type: str = "related_to",
        weight: float = 1.0,
    ) -> "KnowledgeRelation":
        return cls(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
        )


# Standard relation types
RELATION_TYPES = {
    "belongs_to": "BELONGS_TO",
    "related_to": "RELATED_TO",
    "similar_to": "SIMILAR_TO",
    "part_of": "PART_OF",
    "created_by": "CREATED_BY",
    "targets": "TARGETS",
    "mentions": "MENTIONS",
    "derived_from": "DERIVED_FROM",
    "informs": "INFORMS",
}
