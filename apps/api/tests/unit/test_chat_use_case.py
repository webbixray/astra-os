from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.ai.chat_use_case import (
    ChatUseCase,
    build_system_prompt,
    handle_slash_command,
    is_task_request,
)
from app.domain.entities.ai.chat import ChatMessage, ChatRequest, MessageRole


class TestIsTaskRequest:
    def test_create_campaign(self):
        assert is_task_request("create a new campaign") is True

    def test_make_content(self):
        assert is_task_request("make a blog post about AI") is True

    def test_create_social(self):
        assert is_task_request("create a social post") is True
        assert is_task_request("make a social post") is True

    def test_analyze_metrics(self):
        assert is_task_request("analyze campaign performance") is True

    def test_whats_status(self):
        assert is_task_request("what's the status of campaign") is True
        assert is_task_request("what is the performance of") is True

    def test_greeting_is_not_task(self):
        assert is_task_request("hello how are you") is False

    def test_general_question_not_task(self):
        assert is_task_request("what is the weather today") is False

    def test_edge_cases(self):
        assert is_task_request("") is False
        assert is_task_request("  ") is False


class TestHandleSlashCommand:
    def test_help_command(self):
        result = handle_slash_command("/help")
        assert result is not None
        assert "/campaign" in result
        assert "/content" in result

    def test_unknown_command_shows_help(self):
        result = handle_slash_command("/unknown")
        assert result is not None
        assert "Available commands" in result

    def test_non_slash_returns_none(self):
        assert handle_slash_command("create campaign") is None

    def test_empty_string_returns_none(self):
        assert handle_slash_command("") is None


class TestBuildSystemPrompt:
    def test_base_prompt(self):
        prompt = build_system_prompt({})
        assert isinstance(prompt, str)

    def test_with_page_context(self):
        prompt = build_system_prompt({"page": "campaigns", "campaign": "Campaign A"})
        assert "Current page: campaigns" in prompt
        assert "Campaign context: Campaign A" in prompt

    def test_with_memory_notes(self):
        prompt = build_system_prompt({}, memory_notes="User likes email campaigns")
        assert "User likes email campaigns" in prompt


class TestChatUseCase:
    async def test_execute_returns_slash_help(self):
        use_case = ChatUseCase()
        request = ChatRequest(organization_id="org1", user_id="user1", message="/help")
        result = await use_case.execute(request)
        assert "/campaign" in result

    async def test_execute_returns_direct_response(self):
        mock_router = self._mock_router(return_value="Direct response")
        use_case = ChatUseCase(router=mock_router)
        request = ChatRequest(organization_id="org1", user_id="user1", message="hello")
        result = await use_case.execute(request)
        assert result == "Direct response"

    async def test_execute_delegates_to_orchestrator_for_tasks(self):
        mock_router = self._mock_router(return_value="")
        mock_orchestrator = self._mock_orchestrator(
            return_value={"agents_involved": ["CampaignAgent"], "response": "Task done"}
        )
        use_case = ChatUseCase(router=mock_router, orchestrator=mock_orchestrator)
        request = ChatRequest(organization_id="org1", user_id="user1", message="create a campaign")
        result = await use_case.execute(request)
        assert "Task done" in result

    async def test_execute_with_memory(self):
        mock_router = self._mock_router(return_value="Response with context")
        mock_memory = self._mock_memory(
            recall_return=[{"key": "pref", "value": "likes email"}]
        )
        use_case = ChatUseCase(router=mock_router, memory_service=mock_memory)
        request = ChatRequest(organization_id="org1", user_id="user1", message="hello")
        result = await use_case.execute(request)
        assert result == "Response with context"

    async def test_execute_with_message_history(self):
        mock_router = self._mock_router(return_value="Final answer")
        use_case = ChatUseCase(router=mock_router)
        messages = [
            ChatMessage(role=MessageRole.USER, content="hi"),
            ChatMessage(role=MessageRole.ASSISTANT, content="hello"),
        ]
        request = ChatRequest(
            organization_id="org1", user_id="user1", message="help me", messages=messages
        )
        result = await use_case.execute(request)
        assert result == "Final answer"
        messages_arg = mock_router.chat.await_args.args[0]
        contents = [m["content"] for m in messages_arg]
        assert any("hi" in c for c in contents)
        assert any("hello" in c for c in contents)

    async def test_stream_yields_slash_help_characters(self):
        use_case = ChatUseCase()
        request = ChatRequest(organization_id="org1", user_id="user1", message="/help")
        chunks = [c async for c in use_case.stream(request)]
        assert len(chunks) > 0
        output = "".join(chunks)
        assert "/campaign" in output

    async def test_stream_yields_router_chunks(self):
        async def gen():
            for chunk in ["Hello", " ", "World"]:
                yield chunk

        mock_router = self._mock_router(stream=gen)
        use_case = ChatUseCase(router=mock_router)
        request = ChatRequest(organization_id="org1", user_id="user1", message="hello")
        chunks = [c async for c in use_case.stream(request)]
        assert "".join(chunks) == "Hello World"

    @staticmethod
    def _mock_router(return_value="", stream=None):
        router = MagicMock()
        router.chat = AsyncMock(return_value=return_value)
        if stream:
            router.stream_chat = MagicMock(return_value=stream())
        else:
            router.stream_chat = MagicMock()
        return router

    @staticmethod
    def _mock_orchestrator(return_value=None):
        orch = MagicMock()
        orch.process_user_request = AsyncMock(return_value=return_value)
        return orch

    @staticmethod
    def _mock_memory(recall_return=None):
        mem = MagicMock()
        mem.recall = AsyncMock(return_value=recall_return or [])
        mem.capture_conversation = AsyncMock()
        return mem
