from uuid import UUID

from app.domain.entities.content.content import Content
from app.domain.entities.content.content_publish import ContentPublish
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.domain.services.publishing.adapters import get_adapter
from app.infrastructure.db.repositories.content.content_publish_repository import (
    ContentPublishRepository,
)
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl


def _to_response(p: ContentPublish) -> dict:
    return {
        "id": str(p.id),
        "content_id": str(p.content_id),
        "platform": p.platform,
        "status": p.status,
        "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "external_url": p.external_url,
        "error_message": p.error_message,
        "created_at": p.created_at.isoformat(),
    }


class ContentPublishingService:
    def __init__(self, repo: ContentPublishRepository, content_repo: ContentRepositoryImpl | None = None):
        self.repo = repo
        self._content_repo = content_repo

    async def _get_content(self, content_id: UUID) -> Content:
        if self._content_repo is None:
            raise ValidationError("Content repository not available")
        content = await self._content_repo.find_by_id(content_id)
        if content is None:
            raise EntityNotFoundError("Content", str(content_id))
        return content

    async def publish(
        self,
        content_id: UUID,
        platform: str,
        scheduled_at: str | None = None,
        metadata: dict | None = None,
    ) -> ContentPublish:
        from datetime import datetime as dt
        parsed_schedule = dt.fromisoformat(scheduled_at) if scheduled_at else None

        publish = ContentPublish.create(
            content_id=content_id,
            platform=platform,
            scheduled_at=parsed_schedule,
            metadata=metadata,
        )
        saved = await self.repo.save(publish)

        if not parsed_schedule:
            adapter = get_adapter(platform)
            if adapter is None:
                raise ValidationError(f"No adapter found for platform: {platform}")

            saved.mark_publishing()
            await self.repo.save(saved)

            content = await self._get_content(content_id)
            try:
                url = await adapter.publish(content=content, metadata=metadata)
                saved.mark_published(url)
            except Exception as e:
                saved.mark_failed(str(e))

            await self.repo.save(saved)

        return saved

    async def schedule(self, content_id: UUID, platform: str, scheduled_at: str,
                       metadata: dict | None = None) -> ContentPublish:
        from datetime import datetime as dt
        parsed = dt.fromisoformat(scheduled_at)
        publish = ContentPublish.create(
            content_id=content_id,
            platform=platform,
            scheduled_at=parsed,
            metadata=metadata,
        )
        return await self.repo.save(publish)

    async def get_queue(self, org_id: UUID, status: str | None = None) -> list[dict]:
        publishes = await self.repo.find_queue_by_org(org_id, status=status)
        return [_to_response(p) for p in publishes]

    async def get_history(self, content_id: UUID) -> list[dict]:
        publishes = await self.repo.find_by_content(content_id)
        return [_to_response(p) for p in publishes]

    async def cancel(self, publish_id: UUID) -> None:
        publish = await self.repo.find_by_id(publish_id)
        if publish is None:
            raise EntityNotFoundError("ContentPublish", str(publish_id)) from None
        if publish.status not in ("scheduled", "publishing"):
            raise ValidationError(f"Cannot cancel publish in status '{publish.status}'") from None
        await self.repo.delete(publish_id)

    async def retry(self, publish_id: UUID) -> ContentPublish:
        publish = await self.repo.find_by_id(publish_id)
        if publish is None:
            raise EntityNotFoundError("ContentPublish", str(publish_id)) from None
        if publish.status != "failed":
            raise ValidationError("Can only retry failed publishes") from None
        adapter = get_adapter(publish.platform)
        if adapter is None:
            raise ValidationError(f"No adapter found for platform: {publish.platform}") from None
        publish.mark_publishing()
        await self.repo.save(publish)
        content = await self._get_content(publish.content_id)
        try:
            url = await adapter.publish(content=content, metadata=publish.metadata)
            publish.mark_published(url)
        except Exception as e:
            publish.mark_failed(str(e))
        return await self.repo.save(publish)
