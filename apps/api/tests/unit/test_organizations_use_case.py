from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.use_cases.organizations import (
    CreateOrganizationUseCase,
    GetOrganizationUseCase,
    UpdateOrganizationUseCase,
)
from app.domain.entities.organization import Organization
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ForbiddenError


@pytest.fixture
def org_repo():
    return AsyncMock()


@pytest.fixture
def member_repo():
    return AsyncMock()


class TestCreateOrganizationUseCase:
    async def test_create_organization(self, org_repo, member_repo):
        org_repo.find_by_slug.return_value = None
        org_repo.save.return_value = Organization(id=uuid4(), name="Test Org", slug="test-org")
        member_repo.save.return_value = None

        use_case = CreateOrganizationUseCase(org_repo, member_repo)
        result = await use_case.execute("Test Org", "test-org", uuid4())

        assert result.name == "Test Org"
        assert result.slug == "test-org"
        org_repo.save.assert_awaited_once()
        member_repo.save.assert_awaited_once()

    async def test_create_duplicate_slug_raises(self, org_repo, member_repo):
        org_repo.find_by_slug.return_value = Organization(name="Existing", slug="test-org")

        use_case = CreateOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute("Test Org", "test-org", uuid4())

        org_repo.save.assert_not_called()


class TestGetOrganizationUseCase:
    async def test_get_organization(self, org_repo, member_repo):
        org_id = uuid4()
        user_id = uuid4()
        expected_org = Organization(id=org_id, name="Test Org")
        org_repo.find_by_id.return_value = expected_org
        member = AsyncMock()
        member_repo.find_by_user_and_organization.return_value = member

        use_case = GetOrganizationUseCase(org_repo, member_repo)
        result = await use_case.execute(org_id, user_id)

        assert result == expected_org
        org_repo.find_by_id.assert_awaited_with(org_id)

    async def test_get_organization_not_found(self, org_repo, member_repo):
        org_repo.find_by_id.return_value = None

        use_case = GetOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(uuid4(), uuid4())

    async def test_get_organization_forbidden(self, org_repo, member_repo):
        org_repo.find_by_id.return_value = Organization(id=uuid4(), name="Test Org")
        member_repo.find_by_user_and_organization.return_value = None

        use_case = GetOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(ForbiddenError):
            await use_case.execute(uuid4(), uuid4())


class TestUpdateOrganizationUseCase:
    async def test_update_name(self, org_repo, member_repo):
        org_id = uuid4()
        org = Organization(id=org_id, name="Old Name")
        org_repo.find_by_id.return_value = org
        member = AsyncMock()
        member.role = "owner"
        member_repo.find_by_user_and_organization.return_value = member
        org_repo.save.return_value = Organization(id=org_id, name="New Name")

        use_case = UpdateOrganizationUseCase(org_repo, member_repo)
        result = await use_case.execute(org_id, uuid4(), name="New Name")

        assert result.name == "New Name"

    async def test_update_settings(self, org_repo, member_repo):
        org_id = uuid4()
        org = Organization(id=org_id, name="Test")
        org_repo.find_by_id.return_value = org
        org_repo.save.side_effect = lambda o: o
        member = AsyncMock()
        member.role = "admin"
        member_repo.find_by_user_and_organization.return_value = member

        use_case = UpdateOrganizationUseCase(org_repo, member_repo)
        result = await use_case.execute(org_id, uuid4(), settings={"theme": "dark"})

        assert result.settings == {"theme": "dark"}

    async def test_update_org_not_found(self, org_repo, member_repo):
        org_id = uuid4()
        org_repo.find_by_id.return_value = None
        member = AsyncMock()
        member.role = "owner"
        member_repo.find_by_user_and_organization.return_value = member

        use_case = UpdateOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(org_id, uuid4(), name="New Name")

    async def test_update_not_a_member(self, org_repo, member_repo):
        org_repo.find_by_id.return_value = Organization(id=uuid4(), name="Test")
        member_repo.find_by_user_and_organization.return_value = None

        use_case = UpdateOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(ForbiddenError, match="Not a member"):
            await use_case.execute(uuid4(), uuid4(), name="New Name")

    async def test_update_forbidden_for_viewer(self, org_repo, member_repo):
        org_repo.find_by_id.return_value = Organization(id=uuid4(), name="Test")
        member = AsyncMock()
        member.role = "viewer"
        member_repo.find_by_user_and_organization.return_value = member

        use_case = UpdateOrganizationUseCase(org_repo, member_repo)
        with pytest.raises(ForbiddenError, match="admin or owner"):
            await use_case.execute(uuid4(), uuid4(), name="New Name")
