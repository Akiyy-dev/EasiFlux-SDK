from __future__ import annotations

import asyncio
import inspect
import weakref
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

EventHandler = Callable[[Any], Any | Awaitable[Any]]


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: dict[str, list[weakref.ReferenceType[EventHandler]]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler | None = None) -> EventHandler | Callable[[EventHandler], EventHandler]:
        if handler is not None:
            self.add_listener(event, handler)
            return handler

        def decorator(fn: EventHandler) -> EventHandler:
            self.add_listener(event, fn)
            return fn

        return decorator

    def add_listener(self, event: str, handler: EventHandler) -> None:
        self._handlers[event].append(weakref.ref(handler))

    def off(self, event: str, handler: EventHandler) -> None:
        remaining: list[weakref.ReferenceType[EventHandler]] = []
        for ref in self._handlers.get(event, []):
            existing = ref()
            if existing is None:
                continue
            if existing is handler:
                continue
            remaining.append(ref)
        self._handlers[event] = remaining

    async def emit(self, event: str, data: Any) -> None:
        for ref in list(self._handlers.get(event, [])):
            handler = ref()
            if handler is None:
                continue
            result = handler(data)
            if inspect.isawaitable(result):
                await result

    def emit_sync(self, event: str, data: Any) -> None:
        for ref in list(self._handlers.get(event, [])):
            handler = ref()
            if handler is None:
                continue
            result = handler(data)
            if inspect.isawaitable(result):
                asyncio.get_event_loop().create_task(result)
