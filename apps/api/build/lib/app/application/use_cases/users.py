from uuid import UUID

from app.application.ports.repositories import UserRepository
from app.domain.entities.user import User
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


class CreateUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def execute(self, email: str, name: str) -> User:
        existing = await self.repo.find_by_email(email)
        if existing is not None:
            return existing
        user = User.create(email=email, name=name)
        return await self.repo.save(user)


class GetUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def execute(self, user_id: UUID) -> User:
        user = await self.repo.find_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", str(user_id))
        return user


class UpdateUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def execute(
        self, user_id: UUID, name: str | None = None, avatar_url: str | None = None
    ) -> User:
        user = await self.repo.find_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", str(user_id))
        user.update_profile(name=name, avatar_url=avatar_url)
        return await self.repo.save(user)
