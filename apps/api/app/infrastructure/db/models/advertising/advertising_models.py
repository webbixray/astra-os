from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base
from app.infrastructure.db.types import EncryptedJSON


class AdAccountModel(Base):
    __tablename__ = "ad_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    platform_account_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="disconnected")
    currency = Column(String(10), default="USD")
    timezone = Column(String(50), default="America/New_York")
    credentials = Column(EncryptedJSON, default=dict)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdCampaignModel(Base):
    __tablename__ = "ad_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    objective = Column(String(50), default="awareness")
    status = Column(String(50), default="draft")
    platform_campaign_id = Column(String(255), nullable=True)
    platform = Column(String(50), nullable=True)
    daily_budget = Column(Float, default=0)
    lifetime_budget = Column(Float, default=0)
    currency = Column(String(10), default="USD")
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    targeting = Column(JSON, default=dict)
    creatives = Column(JSON, default=list)
    sync_status = Column(String(50), default="not_synced")
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdCreativeModel(Base):
    __tablename__ = "ad_creatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ad_campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    type = Column(String(50), default="image")
    status = Column(String(50), default="draft")
    headline = Column(Text, default="")
    body = Column(Text, default="")
    destination_url = Column(String(1024), default="")
    asset_urls = Column(JSON, default=list)
    platform_creative_ids = Column(JSON, default=dict)
    dimensions = Column(JSON, default=dict)
    thumbnail_url = Column(String(1024), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_domain(self):
        from datetime import UTC

        from app.domain.entities.advertising.ad_creative import (
            AdCreative,
            CreativeStatus,
            CreativeType,
        )

        created = self.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        updated = self.updated_at
        if updated and updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        return AdCreative(
            id=self.id,
            organization_id=self.organization_id,
            ad_campaign_id=self.ad_campaign_id,
            name=self.name,
            type=CreativeType(self.type),
            status=CreativeStatus(self.status),
            headline=self.headline or "",
            body=self.body or "",
            destination_url=self.destination_url or "",
            asset_urls=list(self.asset_urls) if self.asset_urls else [],
            platform_creative_ids=dict(self.platform_creative_ids)
            if self.platform_creative_ids
            else {},
            dimensions=dict(self.dimensions) if self.dimensions else {},
            thumbnail_url=self.thumbnail_url,
            created_by=self.created_by,
            created_at=created.replace(tzinfo=None) if created else None,
            updated_at=updated.replace(tzinfo=None) if updated else None,
        )

    @classmethod
    def from_domain(cls, creative):
        return cls(
            id=creative.id,
            organization_id=creative.organization_id,
            ad_campaign_id=creative.ad_campaign_id,
            name=creative.name,
            type=creative.type.value,
            status=creative.status.value,
            headline=creative.headline,
            body=creative.body,
            destination_url=creative.destination_url,
            asset_urls=creative.asset_urls,
            platform_creative_ids=creative.platform_creative_ids,
            dimensions=creative.dimensions,
            thumbnail_url=creative.thumbnail_url,
            created_by=creative.created_by,
            created_at=creative.created_at,
            updated_at=creative.updated_at,
        )


class AdInsightModel(Base):
    __tablename__ = "ad_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_campaign_id = Column(
        UUID(as_uuid=True), ForeignKey("ad_campaigns.id", ondelete="CASCADE"), nullable=True
    )
    date = Column(String(20), nullable=False, index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Float, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    platform = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        sa.UniqueConstraint("ad_campaign_id", "date", name="uq_insight_per_campaign_date"),
    )
