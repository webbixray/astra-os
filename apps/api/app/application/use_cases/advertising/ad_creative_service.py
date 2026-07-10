from uuid import UUID

from app.domain.entities.advertising.ad_creative import AdCreative, CreativeType
from app.infrastructure.db.repositories.advertising.advertising_repository import (
    AdCreativeRepository,
)


class AdCreativeService:
    def __init__(self, repo: AdCreativeRepository):
        self.repo = repo

    async def create(
        self,
        organization_id: UUID,
        name: str,
        type: str = "image",
        ad_campaign_id: UUID | None = None,
    ) -> dict:
        from app.infrastructure.db.models.advertising.advertising_models import AdCreativeModel

        creative = AdCreative.create(
            organization_id=organization_id,
            name=name,
            type=CreativeType(type),
        )

        model = AdCreativeModel(
            id=creative.id,
            organization_id=organization_id,
            name=name,
            type=type,
            ad_campaign_id=ad_campaign_id,
        )
        saved = await self.repo.save(model)

        return {
            "id": str(saved.id),
            "name": saved.name,
            "type": saved.type,
            "status": saved.status,
        }

    async def list_by_organization(self, organization_id: UUID) -> list[dict]:
        models = await self.repo.find_by_organization(organization_id)
        return [
            {
                "id": str(m.id),
                "name": m.name,
                "type": m.type,
                "status": m.status,
                "headline": m.headline,
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in models
        ]

    async def update(
        self,
        creative_id: UUID,
        headline: str | None = None,
        body: str | None = None,
        destination_url: str | None = None,
        status: str | None = None,
    ) -> dict:
        model = await self.repo.find_by_id(creative_id)
        if not model:
            return {"error": "Creative not found"}
        if headline is not None:
            model.headline = headline
        if body is not None:
            model.body = body
        if destination_url is not None:
            model.destination_url = destination_url
        if status is not None:
            model.status = status
        await self.repo.save(model)
        return {"id": str(model.id), "status": model.status}
