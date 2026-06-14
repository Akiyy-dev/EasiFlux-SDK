from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from ..core.logging import get_logger

logger = get_logger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class WebSocketClient:
    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self._connection: Any = None
        self._receive_task: asyncio.Task[None] | None = None
        self._handlers: list[MessageHandler] = []
        self._closed = False

    @property
    def connected(self) -> bool:
        return self._connection is not None and not self._closed

    def add_handler(self, handler: MessageHandler) -> None:
        self._handlers.append(handler)

    async def connect(self) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise ImportError("WebSocket support requires the 'websockets' package.") from exc

        logger.debug("Connecting WebSocket: %s", self.ws_url)
        self._connection = await websockets.connect(self.ws_url)
        self._closed = False
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def send(self, payload: dict[str, Any]) -> None:
        if self._connection is None:
            raise RuntimeError("WebSocket is not connected.")
        await self._connection.send(json.dumps(payload, separators=(",", ":")))

    async def close(self) -> None:
        self._closed = True
        if self._receive_task is not None:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def _receive_loop(self) -> None:
        assert self._connection is not None
        try:
            async for raw_message in self._connection:
                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    logger.debug("Ignoring non-JSON WebSocket message")
                    continue
                if not isinstance(message, dict):
                    continue
                for handler in self._handlers:
                    result = handler(message)
                    if asyncio.iscoroutine(result):
                        await result
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("WebSocket receive loop ended: %s", exc)
            self._closed = True
