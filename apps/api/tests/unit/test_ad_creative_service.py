from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.advertising.ad_creative_service import AdCreativeService


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return AdCreativeService(repo=repo)


class TestCreate:
    async def test_create_creative(self, service, repo):
        saved_model = MagicMock()
        saved_model.id = uuid4()
        saved_model.name = "Test Creative"
        saved_model.type = "image"
        saved_model.status = "draft"
        repo.save = AsyncMock(return_value=saved_model)

        result = await service.create(uuid4(), "Test Creative", "image")

        assert result["name"] == "Test Creative"
        assert result["type"] == "image"
        assert result["status"] == "draft"


class TestListByOrganization:
    async def test_empty(self, service, repo):
        repo.find_by_organization = AsyncMock(return_value=[])

        result = await service.list_by_organization(uuid4())

        assert result == []

    async def test_with_creatives(self, service, repo):
        m = MagicMock()
        m.id = uuid4()
        m.name = "Creative 1"
        m.type = "image"
        m.status = "active"
        m.headline = "Test headline"
        m.created_at = None
        repo.find_by_organization = AsyncMock(return_value=[m])

        result = await service.list_by_organization(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Creative 1"
        assert result[0]["created_at"] == ""


class TestUpdate:
    async def test_update_existing(self, service, repo):
        model = MagicMock()
        model.id = uuid4()
        model.status = "active"
        model.headline = ""
        repo.find_by_id = AsyncMock(return_value=model)
        repo.save = AsyncMock(return_value=model)

        result = await service.update(model.id, headline="New Headline", status="active")

        assert result["status"] == "active"
        assert model.headline == "New Headline"

    async def test_update_not_found(self, service, repo):
        repo.find_by_id = AsyncMock(return_value=None)

        result = await service.update(uuid4(), headline="New Headline")

        assert result["error"] == "Creative not found"

    async def test_update_partial(self, service, repo):
        model = MagicMock()
        model.id = uuid4()
        model.status = "draft"
        model.headline = ""
        model.body = ""
        model.destination_url = ""
        repo.find_by_id = AsyncMock(return_value=model)
        repo.save = AsyncMock(return_value=model)

        await service.update(model.id, body="New body content")

        assert model.body == "New body content"
        assert model.headline == ""
        assert model.destination_url == ""
