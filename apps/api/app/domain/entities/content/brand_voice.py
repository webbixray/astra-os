from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now


@dataclass
class BrandVoice:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    tone: str = "professional"
    vocabulary: list[str] = field(default_factory=list)
    style_guide: str = ""
    target_audience: str = ""
    is_active: bool = True
    created_by: UUID | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        name: str,
        tone: str = "professional",
        vocabulary: list[str] | None = None,
        style_guide: str = "",
        target_audience: str = "",
        created_by: UUID | None = None,
    ) -> "BrandVoice":
        if tone not in ("professional", "casual", "funny", "formal", "friendly", "authoritative"):
            msg = f"Invalid tone: {tone}"
            raise ValueError(msg)
        return cls(
            organization_id=organization_id,
            name=name,
            tone=tone,
            vocabulary=vocabulary or [],
            style_guide=style_guide,
            target_audience=target_audience,
            created_by=created_by,
        )
