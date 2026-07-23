from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.domain.entities.user import User

if TYPE_CHECKING:
    from app.domain.entities.prompts import SystemPrompt


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None: ...


class OrganizationRepository(ABC):
    @abstractmethod
    async def save(self, organization: Organization) -> Organization: ...

    @abstractmethod
    async def find_by_id(self, org_id: UUID) -> Organization | None: ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> Organization | None: ...

    @abstractmethod
    async def find_by_parent(self, parent_org_id: UUID) -> list[Organization]: ...

    @abstractmethod
    async def delete(self, org_id: UUID) -> None: ...


class SystemPromptRepository(ABC):
    @abstractmethod
    async def save(self, prompt: "SystemPrompt") -> "SystemPrompt": ...

    @abstractmethod
    async def find_by_id(self, prompt_id: UUID) -> "SystemPrompt | None": ...

    @abstractmethod
    async def find_by_name(
        self, name: str, org_id: UUID | None = None
    ) -> "SystemPrompt | None": ...

    @abstractmethod
    async def list_by_category(
        self, category: str, org_id: UUID | None = None
    ) -> list["SystemPrompt"]: ...

    @abstractmethod
    async def list_all(self, org_id: UUID | None = None) -> list["SystemPrompt"]: ...

    @abstractmethod
    async def delete(self, prompt_id: UUID) -> None: ...


class TeamMemberRepository(ABC):
    @abstractmethod
    async def save(self, member: TeamMember) -> TeamMember: ...

    @abstractmethod
    async def find_by_id(self, member_id: UUID) -> TeamMember | None: ...

    @abstractmethod
    async def find_by_organization(self, org_id: UUID) -> list[TeamMember]: ...

    @abstractmethod
    async def find_by_user_and_organization(
        self, user_id: UUID, org_id: UUID
    ) -> TeamMember | None: ...

    @abstractmethod
    async def delete(self, member_id: UUID) -> None: ...
