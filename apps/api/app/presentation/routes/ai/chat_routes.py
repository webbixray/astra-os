from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.agents.orchestrator import AgentOrchestrator
from app.application.use_cases.agents.tool_registry import ToolRegistry
from app.application.use_cases.ai.chat_use_case import ChatUseCase
from app.application.use_cases.ai.prompt_manager import PromptManager
from app.application.use_cases.knowledge.memory_service import MemoryService
from app.domain.entities.ai.chat import ChatMessage, ChatRequest, MessageRole
from app.infrastructure.db.repositories.prompt_repository import SystemPromptRepositoryImpl
from app.infrastructure.external_adapters.agents.tool_handlers import register_tools
from app.infrastructure.external_adapters.ai.router import AIRouter
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class ChatMessageSchema(BaseModel):
    role: str
    content: str


class ChatRequestSchema(BaseModel):
    organization_id: UUID
    message: str
    conversation_id: str | None = None
    page_context: dict | None = None
    messages: list[ChatMessageSchema] | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


async def get_chat_use_case(
    db: AsyncSession = Depends(get_db),
) -> ChatUseCase:
    registry = ToolRegistry()
    register_tools(registry, db)
    ai_router = AIRouter()
    orchestrator = AgentOrchestrator(tool_registry=registry, ai_router=ai_router)
    graph_store = GraphStore(db)
    memory_service = MemoryService(graph_store)
    prompt_repo = SystemPromptRepositoryImpl(db)
    prompt_manager = PromptManager(repository=prompt_repo)
    return ChatUseCase(
        router=ai_router,
        orchestrator=orchestrator,
        memory_service=memory_service,
        prompt_manager=prompt_manager,
    )


@router.post("/chat/stream", summary="Stream chat response")
async def chat_stream(
    request: ChatRequestSchema,
    use_case: ChatUseCase = Depends(get_chat_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    await require_org_role(request.organization_id, "member", user_id, db)
    domain_messages = []
    if request.messages:
        domain_messages = [
            ChatMessage(role=MessageRole(m.role), content=m.content) for m in request.messages
        ]

    domain_request = ChatRequest(
        organization_id=str(request.organization_id),
        user_id=str(user_id),
        message=request.message,
        conversation_id=request.conversation_id,
        page_context=request.page_context,
        messages=domain_messages,
    )

    async def generate():
        async for chunk in use_case.stream(domain_request):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", response_model=ChatResponse, summary="Send a chat message")
async def chat(
    request: ChatRequestSchema,
    use_case: ChatUseCase = Depends(get_chat_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    domain_messages = []
    if request.messages:
        domain_messages = [
            ChatMessage(role=MessageRole(m.role), content=m.content) for m in request.messages
        ]

    domain_request = ChatRequest(
        organization_id=str(request.organization_id),
        user_id=str(user_id),
        message=request.message,
        conversation_id=request.conversation_id,
        page_context=request.page_context,
        messages=domain_messages,
    )

    response = await use_case.execute(domain_request)
    return {"response": response, "conversation_id": domain_request.conversation_id}
