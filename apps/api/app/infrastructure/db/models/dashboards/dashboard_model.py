import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.dashboards.dashboard import Dashboard, DashboardWidget
from app.infrastructure.db.base import Base


class DashboardModel(Base):
    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    layout_columns: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> Dashboard:
        return Dashboard(
            id=self.id, organization_id=self.organization_id, name=self.name,
            description=self.description, layout_columns=self.layout_columns,
            is_default=self.is_default, created_by=self.created_by,
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, d: Dashboard) -> "DashboardModel":
        return cls(
            id=d.id, organization_id=d.organization_id, name=d.name,
            description=d.description, layout_columns=d.layout_columns,
            is_default=d.is_default, created_by=d.created_by,
            created_at=d.created_at, updated_at=d.updated_at,
        )


class DashboardWidgetModel(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    pos_x: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pos_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def to_domain(self) -> DashboardWidget:
        return DashboardWidget(
            id=self.id, dashboard_id=self.dashboard_id, widget_type=self.widget_type,
            title=self.title, pos_x=self.pos_x, pos_y=self.pos_y,
            width=self.width, height=self.height,
            config=dict(self.config) if self.config else {},
            created_at=self.created_at.replace(tzinfo=None),
            updated_at=self.updated_at.replace(tzinfo=None),
        )

    @classmethod
    def from_domain(cls, w: DashboardWidget) -> "DashboardWidgetModel":
        return cls(
            id=w.id, dashboard_id=w.dashboard_id, widget_type=w.widget_type,
            title=w.title, pos_x=w.pos_x, pos_y=w.pos_y,
            width=w.width, height=w.height, config=w.config,
            created_at=w.created_at, updated_at=w.updated_at,
        )
