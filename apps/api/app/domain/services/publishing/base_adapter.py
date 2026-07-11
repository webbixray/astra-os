from abc import ABC, abstractmethod

from app.domain.entities.content.content import Content


class PublishingAdapter(ABC):
    @abstractmethod
    async def publish(self, content: Content, metadata: dict | None = None) -> str: ...

    @abstractmethod
    def platform(self) -> str: ...
