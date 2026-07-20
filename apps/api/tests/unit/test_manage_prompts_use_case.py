from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.ai.manage_prompts_use_case import ManagePromptsUseCase
from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.list_by_category = AsyncMock(return_value=[])
    repo.list_all = AsyncMock(return_value=[])
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_manager(mock_repo):
    mgr = MagicMock()
    mgr.repository = mock_repo
    mgr.save_prompt = AsyncMock()
    return mgr


@pytest.fixture
def use_case(mock_manager):
    return ManagePromptsUseCase(prompt_manager=mock_manager)


class TestManagePromptsUseCase:
    async def test_list_prompts_delegates_to_repo(self, use_case, mock_repo):
        expected = [
            SystemPrompt.create(name="a", content="a"),
            SystemPrompt.create(name="b", content="b"),
        ]
        mock_repo.list_all.return_value = expected
        result = await use_case.list_prompts()
        assert result == expected
        mock_repo.list_all.assert_awaited_once()

    async def test_list_prompts_by_category(self, use_case, mock_repo):
        expected = [SystemPrompt.create(name="a", content="a", category=PromptCategory.CONTENT)]
        mock_repo.list_by_category.return_value = expected
        result = await use_case.list_prompts(category="content")
        assert result == expected
        mock_repo.list_by_category.assert_awaited_once_with("content", org_id=None)

    async def test_list_prompts_with_org_filter(self, use_case, mock_repo):
        org_id = uuid4()
        await use_case.list_prompts(org_id=org_id)
        mock_repo.list_all.assert_awaited_once_with(org_id=org_id)

    async def test_list_prompts_returns_empty_when_no_repo(self, use_case):
        use_case.prompt_manager.repository = None
        result = await use_case.list_prompts()
        assert result == []

    async def test_get_prompt_delegates_to_repo(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="test")
        pid = prompt.id
        mock_repo.find_by_id.return_value = prompt
        result = await use_case.get_prompt(pid)
        assert result is prompt
        mock_repo.find_by_id.assert_awaited_once_with(pid)

    async def test_get_prompt_returns_none_when_no_repo(self, use_case):
        use_case.prompt_manager.repository = None
        result = await use_case.get_prompt(uuid4())
        assert result is None

    async def test_create_prompt(self, use_case, mock_repo, mock_manager):
        expected = SystemPrompt.create(name="test", content="content")
        mock_manager.save_prompt.return_value = expected
        result = await use_case.create_prompt(
            name="test",
            content="content",
            category=PromptCategory.SYSTEM,
            description="desc",
            org_id=uuid4(),
            variables=["var1"],
            created_by=uuid4(),
        )
        assert result is expected
        mock_manager.save_prompt.assert_awaited_once()

    async def test_update_prompt(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="original")
        mock_repo.find_by_id.return_value = prompt
        mock_repo.save.return_value = prompt
        result = await use_case.update_prompt(prompt.id, content="updated")
        assert result.content == "updated"
        assert result.version == 2
        mock_repo.save.assert_awaited_once_with(prompt)

    async def test_update_prompt_raises_when_not_found(self, use_case, mock_repo):
        mock_repo.find_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await use_case.update_prompt(uuid4(), content="updated")

    async def test_update_prompt_raises_without_repo(self, use_case):
        use_case.prompt_manager.repository = None
        with pytest.raises(RuntimeError):
            await use_case.update_prompt(uuid4(), content="updated")

    async def test_update_prompt_does_not_bump_when_content_same(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="same")
        mock_repo.find_by_id.return_value = prompt
        mock_repo.save.return_value = prompt
        result = await use_case.update_prompt(prompt.id, content="same")
        assert result.version == 1

    async def test_update_prompt_sets_status(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="test")
        mock_repo.find_by_id.return_value = prompt
        mock_repo.save.return_value = prompt
        result = await use_case.update_prompt(prompt.id, status=PromptStatus.ARCHIVED)
        assert result.status == PromptStatus.ARCHIVED

    async def test_update_prompt_sets_description(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="test")
        mock_repo.find_by_id.return_value = prompt
        mock_repo.save.return_value = prompt
        result = await use_case.update_prompt(prompt.id, description="new desc")
        assert result.description == "new desc"

    async def test_update_prompt_sets_variables(self, use_case, mock_repo):
        prompt = SystemPrompt.create(name="test", content="test")
        mock_repo.find_by_id.return_value = prompt
        mock_repo.save.return_value = prompt
        result = await use_case.update_prompt(prompt.id, variables=["a", "b"])
        assert result.variables == ["a", "b"]

    async def test_delete_prompt(self, use_case, mock_repo):
        pid = uuid4()
        await use_case.delete_prompt(pid)
        mock_repo.delete.assert_awaited_once_with(pid)

    async def test_delete_prompt_skips_without_repo(self, use_case):
        use_case.prompt_manager.repository = None
        await use_case.delete_prompt(uuid4())  # should not raise
