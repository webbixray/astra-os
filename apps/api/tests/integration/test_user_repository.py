import pytest

from app.domain.entities.user import User
from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl


@pytest.mark.asyncio
class TestUserRepository:
    async def test_save_and_find_by_id(self, db_session):
        repo = UserRepositoryImpl(db_session)
        user = User.create(email="save@test.com", name="Save Test")
        saved = await repo.save(user)
        assert saved.id is not None
        assert saved.email == "save@test.com"

        found = await repo.find_by_id(saved.id)
        assert found is not None
        assert found.email == "save@test.com"

    async def test_find_by_email(self, db_session):
        repo = UserRepositoryImpl(db_session)
        user = User.create(email="find@test.com", name="Find Test")
        await repo.save(user)

        found = await repo.find_by_email("find@test.com")
        assert found is not None
        assert found.name == "Find Test"

        not_found = await repo.find_by_email("nonexistent@test.com")
        assert not_found is None

    async def test_delete_user(self, db_session):
        repo = UserRepositoryImpl(db_session)
        user = User.create(email="delete@test.com", name="Delete Test")
        saved = await repo.save(user)

        await repo.delete(saved.id)
        found = await repo.find_by_id(saved.id)
        assert found is None
