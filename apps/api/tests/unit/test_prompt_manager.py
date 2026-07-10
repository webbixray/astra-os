from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.ai.prompt_manager import BUILTIN_PROMPTS, PromptManager
from app.domain.entities.prompts import PromptStatus, SystemPrompt


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.list_by_category = AsyncMock()
    repo.list_all = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def manager(mock_repo):
    return PromptManager(repository=mock_repo)


class TestPromptManager:
    async def test_get_prompt_returns_org_prompt_first(self, manager, mock_repo):
        org_prompt = SystemPrompt.create(name="test", content="Org version", org_id=uuid4())
        mock_repo.find_by_name.side_effect = lambda name, org_id=None: (
            org_prompt if org_id is not None else None
        )
        result = await manager.get_prompt("test", org_id=uuid4())
        assert result == "Org version"

    async def test_get_prompt_falls_back_to_global(self, manager, mock_repo):
        global_prompt = SystemPrompt.create(name="test", content="Global version")
        mock_repo.find_by_name.side_effect = lambda name, org_id=None: (
            None if org_id is not None else global_prompt
        )
        result = await manager.get_prompt("test", org_id=uuid4())
        assert result == "Global version"

    async def test_get_prompt_skips_non_active_org_prompt(self, manager, mock_repo):
        draft_prompt = SystemPrompt.create(name="test", content="Draft")
        draft_prompt.status = PromptStatus.DRAFT
        global_prompt = SystemPrompt.create(name="test", content="Active global")
        mock_repo.find_by_name.side_effect = lambda name, org_id=None: (
            draft_prompt if org_id is not None else global_prompt
        )
        result = await manager.get_prompt("test", org_id=uuid4())
        assert result == "Active global"

    async def test_get_prompt_uses_builtin_when_no_db(self, manager):
        manager.repository = None
        result = await manager.get_prompt("system_chat")
        assert "ASTRA" in result

    async def test_get_prompt_uses_builtin_when_not_in_db(self, manager, mock_repo):
        mock_repo.find_by_name.return_value = None
        result = await manager.get_prompt("system_chat", org_id=uuid4())
        assert "ASTRA" in result

    async def test_get_prompt_returns_empty_string_for_unknown(self, manager, mock_repo):
        mock_repo.find_by_name.return_value = None
        result = await manager.get_prompt("nonexistent")
        assert result == ""

    async def test_get_prompt_renders_variables(self, manager, mock_repo):
        prompt = SystemPrompt.create(name="greeting", content="Hello {{name}}!")
        mock_repo.find_by_name.return_value = prompt
        result = await manager.get_prompt("greeting", variables={"name": "Alice"})
        assert result == "Hello Alice!"

    async def test_get_prompt_keeps_unresolved_placeholder(self, manager, mock_repo):
        prompt = SystemPrompt.create(name="test", content="Hello {{name}}!")
        mock_repo.find_by_name.return_value = prompt
        result = await manager.get_prompt("test")
        assert result == "Hello {{name}}!"

    async def test_get_prompt_entity_returns_org_prompt(self, manager, mock_repo):
        org_prompt = SystemPrompt.create(name="test", content="test", org_id=uuid4())
        global_prompt = SystemPrompt.create(name="test", content="test")
        mock_repo.find_by_name.side_effect = lambda name, org_id=None: (
            org_prompt if org_id is not None else global_prompt
        )
        result = await manager.get_prompt_entity("test", org_id=uuid4())
        assert result is org_prompt

    async def test_get_prompt_entity_falls_back(self, manager, mock_repo):
        global_prompt = SystemPrompt.create(name="test", content="test")
        mock_repo.find_by_name.side_effect = lambda name, org_id=None: (
            None if org_id is not None else global_prompt
        )
        result = await manager.get_prompt_entity("test", org_id=uuid4())
        assert result is global_prompt

    async def test_get_prompt_entity_returns_none_when_no_repo(self, manager):
        manager.repository = None
        result = await manager.get_prompt_entity("test")
        assert result is None

    async def test_save_prompt_calls_repo_save(self, manager, mock_repo):
        prompt = SystemPrompt.create(name="test", content="Hello")
        mock_repo.save.return_value = prompt
        result = await manager.save_prompt(prompt)
        assert result is prompt
        mock_repo.save.assert_awaited_once_with(prompt)

    async def test_save_prompt_raises_without_repo(self, manager):
        manager.repository = None
        with pytest.raises(RuntimeError, match="has no repository configured"):
            await manager.save_prompt(SystemPrompt.create(name="test", content="test"))

    async def test_seed_builtins_seeds_new_prompts(self, manager, mock_repo):
        mock_repo.find_by_name.return_value = None
        count = await manager.seed_builtins()
        expected = len(BUILTIN_PROMPTS)
        assert count == expected
        assert mock_repo.save.await_count == expected

    async def test_seed_builtins_skips_existing(self, manager, mock_repo):
        mock_repo.find_by_name.return_value = MagicMock()
        count = await manager.seed_builtins()
        assert count == 0
        mock_repo.save.assert_not_called()

    async def test_seed_builtins_returns_zero_without_repo(self, manager):
        manager.repository = None
        count = await manager.seed_builtins()
        assert count == 0

    async def test_set_repository(self, manager):
        new_repo = MagicMock()
        manager.set_repository(new_repo)
        assert manager.repository is new_repo

    def test_render_replaces_single_variable(self):
        result = PromptManager._render("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_render_replaces_multiple_variables(self):
        result = PromptManager._render("{{a}} {{b}}", {"a": "1", "b": "2"})
        assert result == "1 2"

    def test_render_handles_no_variables(self):
        result = PromptManager._render("Hello World!", {})
        assert result == "Hello World!"

    def test_render_handles_empty_template(self):
        result = PromptManager._render("", {"x": "y"})
        assert result == ""

    def test_render_preserves_unmatched_variable(self):
        result = PromptManager._render("Hello {{name}}!", {})
        assert result == "Hello {{name}}!"
