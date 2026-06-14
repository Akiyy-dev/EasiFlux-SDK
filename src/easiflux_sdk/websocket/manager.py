from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..config import AuthConfig
from ..core.auth import Signer
from ..core.events import EventEmitter
from ..core.logging import get_logger
from ..core.time_sync import TimeSyncManager
from .client import WebSocketClient
from .private import PRIVATE_CHANNELS, authenticate_private, subscribe_private
from .public import subscribe_public
from .reconnect import ReconnectPolicy

logger = get_logger(__name__)

Callback = Callable[[dict[str, Any]], Awaitable[None] | None]


@dataclass
class Subscription:
    channel: str
    params: dict[str, Any]
    callback: Callback | None = None
    private: bool = False


class WebSocketManager:
    def __init__(
        self,
        *,
        ws_url: str,
        api_key: str,
        api_secret: str,
        auth_config: AuthConfig,
        signer: Signer,
        time_sync: TimeSyncManager,
        events: EventEmitter,
        reconnect_policy: ReconnectPolicy | None = None,
    ) -> None:
        self.ws_url = ws_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.auth_config = auth_config
        self.signer = signer
        self.time_sync = time_sync
        self.events = events
        self.reconnect_policy = reconnect_policy or ReconnectPolicy()

        self._client = WebSocketClient(ws_url)
        self._subscriptions: list[Subscription] = []
        self._authenticated = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._client.add_handler(self._dispatch_message)

    async def connect(self) -> None:
        await self._client.connect()
        self._monitor_task = asyncio.create_task(self._monitor_connection())
        await self._restore_subscriptions()

    async def subscribe(
        self,
        channel: str,
        params: dict[str, Any] | None = None,
        *,
        callback: Callback | None = None,
    ) -> None:
        params = params or {}
        private = channel in PRIVATE_CHANNELS
        subscription = Subscription(channel=channel, params=params, callback=callback, private=private)
        self._subscriptions.append(subscription)

        if not self._client.connected:
            await self.connect()
            return

        await self._apply_subscription(subscription)

    async def close(self) -> None:
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await self._client.close()

    async def _apply_subscription(self, subscription: Subscription) -> None:
        if subscription.private:
            if not self._authenticated:
                await authenticate_private(self._client.send, signer=self.signer, time_sync=self.time_sync)
                self._authenticated = True
            await subscribe_private(self._client.send, subscription.channel, subscription.params)
        else:
            await subscribe_public(self._client.send, subscription.channel, subscription.params)

    async def _restore_subscriptions(self) -> None:
        self._authenticated = False
        for subscription in self._subscriptions:
            await self._apply_subscription(subscription)

    async def _monitor_connection(self) -> None:
        attempt = 0
        while True:
            await asyncio.sleep(self.reconnect_policy.heartbeat_interval)
            if self._client.connected:
                attempt = 0
                continue

            if attempt >= self.reconnect_policy.max_retries:
                logger.debug("WebSocket reconnect attempts exhausted")
                return

            delay = self.reconnect_policy.backoff_delay(attempt)
            logger.debug("WebSocket reconnecting in %.1fs (attempt %s)", delay, attempt + 1)
            await asyncio.sleep(delay)
            attempt += 1

            try:
                await self._client.connect()
                await self._restore_subscriptions()
                attempt = 0
            except Exception as exc:
                logger.debug("WebSocket reconnect failed: %s", exc)

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        channel = str(message.get("channel") or message.get("topic") or "")
        if channel:
            event_name = channel.split(".")[0] if "." in channel else channel
            await self.events.emit(event_name, message)
            await self.events.emit("market", message)

        for subscription in self._subscriptions:
            if subscription.callback is None:
                continue
            if channel and subscription.channel not in channel:
                continue
            result = subscription.callback(message)
            if asyncio.iscoroutine(result):
                await result

            if subscription.channel in {"order", "position", "balance"}:
                await self.events.emit(subscription.channel, message)
