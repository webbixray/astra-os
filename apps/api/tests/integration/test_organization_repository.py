import pytest

from app.domain.entities.organization import Organization
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl


@pytest.mark.asyncio
class TestOrganizationRepository:
    async def test_save_and_find(self, db_session):
        repo = OrganizationRepositoryImpl(db_session)
        org = Organization.create(name="Test Org", slug="test-org")
        saved = await repo.save(org)
        assert saved.slug == "test-org"

        found = await repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "Test Org"

        found_by_slug = await repo.find_by_slug("test-org")
        assert found_by_slug is not None

    async def test_unique_slug(self, db_session):
        repo = OrganizationRepositoryImpl(db_session)
        org1 = Organization.create(name="Org 1", slug="same-slug")
        await repo.save(org1)

        org2 = Organization.create(name="Org 2", slug="same-slug")
        with pytest.raises(Exception):
            await repo.save(org2)
