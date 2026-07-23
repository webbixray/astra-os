import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.team_member import TeamMember
from app.infrastructure.db.base import Base


class TeamMemberModel(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_team_member_org_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def to_domain(self) -> TeamMember:
        return TeamMember(
            id=self.id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            role=self.role,
            permissions=list(self.permissions) if self.permissions else [],
            joined_at=self.joined_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, member: TeamMember) -> "TeamMemberModel":
        return cls(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            role=member.role,
            permissions=member.permissions,
            joined_at=member.joined_at,
        )
