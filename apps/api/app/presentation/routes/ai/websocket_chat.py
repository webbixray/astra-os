from __future__ import annotations

import json
import logging
import uuid
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.application.use_cases.agents.orchestrator import AgentOrchestrator
from app.application.use_cases.agents.tool_registry import ToolRegistry
from app.application.use_cases.ai.chat_use_case import ChatUseCase
from app.application.use_cases.ai.prompt_manager import PromptManager
from app.application.use_cases.knowledge.memory_service import MemoryService
from app.domain.entities.ai.chat import ChatMessage, ChatRequest, MessageRole
from app.infrastructure.auth.jwt import JWTService
from app.infrastructure.auth.supabase_jwt import SupabaseJWTVerifier
from app.infrastructure.db.repositories.prompt_repository import SystemPromptRepositoryImpl
from app.infrastructure.external_adapters.ai.router import AIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

_jwt_service = JWTService()
_supabase_verifier = SupabaseJWTVerifier()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info("WebSocket connected: %s", client_id)

    def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)
        logger.info("WebSocket disconnected: %s", client_id)

    async def send_json(self, client_id: str, data: dict[str, Any]) -> None:
        ws = self._connections.get(client_id)
        if ws and ws.client_state == WebSocketState.CONNECTED:
            await ws.send_json(data)


manager = ConnectionManager()


async def _verify_ws_token(token: str) -> UUID | None:
    """Verify a JWT token and return the user ID, or None if invalid."""
    if _supabase_verifier.enabled:
        payload = await _supabase_verifier.verify_token(token)
        if payload is not None:
            sub = payload.get("sub")
            if sub:
                try:
                    return UUID(sub)
                except ValueError:
                    pass
    payload = _jwt_service.verify_token(token)
    if payload is not None:
        sub = payload.get("sub")
        if sub:
            try:
                return UUID(sub)
            except ValueError:
                pass
    return None


def _build_use_case() -> ChatUseCase:
    registry = ToolRegistry()
    ai_router = AIRouter()
    orchestrator = AgentOrchestrator(tool_registry=registry, ai_router=ai_router)
    graph_store = None
    memory_service = MemoryService(graph_store) if graph_store else None
    prompt_repo = SystemPromptRepositoryImpl.__new__(SystemPromptRepositoryImpl)
    prompt_manager = PromptManager(repository=prompt_repo)
    return ChatUseCase(
        router=ai_router,
        orchestrator=orchestrator,
        memory_service=memory_service,
        prompt_manager=prompt_manager,
    )


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    # Authenticate via token query parameter
    user_id: UUID | None = None
    if token:
        user_id = await _verify_ws_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Authentication required")
        logger.warning("WebSocket connection rejected: missing or invalid token")
        return

    client_id = str(user_id)

    try:
        await manager.connect(websocket, client_id)
        await manager.send_json(client_id, {
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to ASTRA OS chat",
        })

        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "Invalid JSON payload",
                })
                continue

            message = payload.get("message", "")
            conversation_id = payload.get("conversation_id", str(uuid.uuid4()))
            organization_id = payload.get("organization_id", "")
            history = payload.get("messages", [])

            if not message:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "Message is required",
                })
                continue

            await manager.send_json(client_id, {
                "type": "thinking",
                "conversation_id": conversation_id,
            })

            try:
                domain_messages = [
                    ChatMessage(role=MessageRole(m["role"]), content=m["content"])
                    for m in history if isinstance(m, dict) and "role" in m and "content" in m
                ]

                domain_request = ChatRequest(
                    organization_id=organization_id,
                    user_id=str(user_id),
                    message=message,
                    conversation_id=conversation_id,
                    messages=domain_messages,
                )

                full_response = ""
                use_case = _build_use_case()

                async for chunk in use_case.stream(domain_request):
                    full_response += chunk
                    await manager.send_json(client_id, {
                        "type": "chunk",
                        "content": chunk,
                        "conversation_id": conversation_id,
                    })

                await manager.send_json(client_id, {
                    "type": "done",
                    "conversation_id": conversation_id,
                    "full_response": full_response,
                })

            except Exception:
                logger.exception("WebSocket chat error for user %s", user_id)
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "An error occurred while processing your message",
                    "conversation_id": conversation_id,
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        logger.exception("WebSocket connection error for user %s", user_id)
        manager.disconnect(client_id)
