from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


def _is_enveloped(body: dict) -> bool:
    return "success" in body and ("data" in body or "code" in body)


DEFAULT_EXCLUDE_PREFIXES = (
    "/api/v1/health",
    "/api/v1/metrics",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
)


class EnvelopeMiddleware:
    def __init__(self, app: ASGIApp, exclude_prefixes: tuple[str, ...] | None = None) -> None:
        self.app = app
        self.exclude_prefixes = exclude_prefixes or DEFAULT_EXCLUDE_PREFIXES

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path.startswith(self.exclude_prefixes):
            await self.app(scope, receive, send)
            return

        send_buffer: list[dict[str, Any]] = []

        async def capturing_send(message: dict[str, Any]) -> None:
            send_buffer.append(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                await self._send_enveloped(send_buffer, send)
            elif message["type"] == "http.response.start":
                pass
            elif message["type"] != "http.response.body":
                await send(message)

        await self.app(scope, receive, capturing_send)

    async def _send_enveloped(self, buffer: list[dict[str, Any]], send: Send) -> None:
        start = buffer[0] if buffer and buffer[0]["type"] == "http.response.start" else None
        body_chunks = [m for m in buffer if m["type"] == "http.response.body" and m.get("body")]
        if not start or not body_chunks:
            for msg in buffer:
                await send(msg)
            return

        status_code = start.get("status", 200)
        if not 200 <= status_code < 300:
            for msg in buffer:
                await send(msg)
            return

        raw_body = b"".join(m["body"] for m in body_chunks)
        try:
            decoded = json.loads(raw_body)
        except (ValueError, TypeError):
            for msg in buffer:
                await send(msg)
            return

        if isinstance(decoded, dict) and _is_enveloped(decoded):
            for msg in buffer:
                await send(msg)
            return

        wrapped = {"success": True, "data": decoded}
        wrapped_bytes = json.dumps(wrapped, default=str).encode("utf-8")

        start["headers"] = [
            (k, v)
            for k, v in start.get("headers", [])
            if k.lower() not in {"content-length", "content-encoding"}
        ]
        start["headers"].append((b"content-length", str(len(wrapped_bytes)).encode("utf-8")))

        await send(start)
        await send({"type": "http.response.body", "body": wrapped_bytes, "more_body": False})
