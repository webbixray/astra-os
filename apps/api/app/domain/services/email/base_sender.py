from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: list[str], subject: str, body: str,
                   from_email: str, from_name: str = "",
                   metadata: dict | None = None) -> dict:
        ...

    @abstractmethod
    def provider_type(self) -> str:
        ...
