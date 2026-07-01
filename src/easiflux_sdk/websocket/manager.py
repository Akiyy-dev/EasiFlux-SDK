from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..config import DEFAULT_WS_URLS, AuthConfig
from ..core.auth import Signer
from ..core.events import EventEmitter
from ..core.logging import get_logger
from ..core.time_sync import TimeSyncManager
from .client import WebSocketClient
from .private import PRIVATE_TOPICS, authenticate_private, subscribe_private
from .public import build_ping_message, subscribe_public
from .reconnect import ReconnectPolicy

logger = get_logger(__name__)

Callback = Callable[[dict[str, Any]], Awaitable[None] | None]

_LEGACY_CHANNEL_ALIASES = {
    "tickers-100": "ticker",
    "ob_snap_shot": "depth",
    "trades-100": "trades",
    "contract.position": "position",
    "contract.order": "order",
    "contract.execution": "execution",
    "contract.wallet": "wallet",
    "candle": "candle",
}


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
        ws_public_url: str | None = None,
        ws_private_url: str | None = None,
        ws_url: str | None = None,
        api_key: str,
        api_secret: str,
        auth_config: AuthConfig,
        signer: Signer,
        time_sync: TimeSyncManager,
        events: EventEmitter,
        reconnect_policy: ReconnectPolicy | None = None,
    ) -> None:
        if ws_url is not None and ws_public_url is None:
            ws_public_url = ws_url

        self.ws_public_url = ws_public_url or DEFAULT_WS_URLS["contract_public"]
        self.ws_private_url = ws_private_url or DEFAULT_WS_URLS["contract_private"]
        self.api_key = api_key
        self.api_secret = api_secret
        self.auth_config = auth_config
        self.signer = signer
        self.time_sync = time_sync
        self.events = events
        self.reconnect_policy = reconnect_policy or ReconnectPolicy(heartbeat_interval=15.0)

        self._public_client = WebSocketClient(self.ws_public_url)
        self._private_client = WebSocketClient(self.ws_private_url)
        self._subscriptions: list[Subscription] = []
        self._authenticated = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

        self._public_client.add_handler(self._dispatch_message)
        self._private_client.add_handler(self._dispatch_message)

    async def connect(self) -> None:
        await self._public_client.connect()
        if self._has_private_subscriptions():
            await self._private_client.connect()
            await authenticate_private(self._private_client.send, signer=self.signer)
            self._authenticated = True

        self._monitor_task = asyncio.create_task(self._monitor_connection())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        await self._restore_subscriptions()

    async def subscribe(
        self,
        channel: str,
        params: dict[str, Any] | None = None,
        *,
        callback: Callback | None = None,
    ) -> None:
        params = params or {}
        private = channel in PRIVATE_TOPICS or channel.startswith("contract.")
        subscription = Subscription(channel=channel, params=params, callback=callback, private=private)
        self._subscriptions.append(subscription)

        if not self._public_client.connected:
            await self.connect()
            return

        await self._apply_subscription(subscription)

    async def close(self) -> None:
        for task in (self._monitor_task, self._heartbeat_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._monitor_task = None
        self._heartbeat_task = None
        await self._public_client.close()
        await self._private_client.close()

    def _has_private_subscriptions(self) -> bool:
        return any(sub.private for sub in self._subscriptions)

    async def _apply_subscription(self, subscription: Subscription) -> None:
        if subscription.private:
            if not self._private_client.connected:
                await self._private_client.connect()
            if not self._authenticated:
                await authenticate_private(self._private_client.send, signer=self.signer)
                self._authenticated = True
            await subscribe_private(
                self._private_client.send,
                subscription.channel,
                subscription.params,
            )
        else:
            if not self._public_client.connected:
                await self._public_client.connect()
            await subscribe_public(
                self._public_client.send,
                subscription.channel,
                subscription.params,
            )

    async def _restore_subscriptions(self) -> None:
        self._authenticated = False
        for subscription in self._subscriptions:
            await self._apply_subscription(subscription)

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.reconnect_policy.heartbeat_interval)
            ping = build_ping_message()
            if self._public_client.connected:
                try:
                    await self._public_client.send(ping)
                except Exception as exc:
                    logger.debug("Public WebSocket ping failed: %s", exc)
            if self._private_client.connected:
                try:
                    await self._private_client.send(ping)
                except Exception as exc:
                    logger.debug("Private WebSocket ping failed: %s", exc)

    async def _monitor_connection(self) -> None:
        attempt = 0
        while True:
            await asyncio.sleep(self.reconnect_policy.heartbeat_interval)
            public_ok = self._public_client.connected
            private_ok = not self._has_private_subscriptions() or self._private_client.connected
            if public_ok and private_ok:
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
                if not public_ok:
                    await self._public_client.connect()
                if self._has_private_subscriptions() and not private_ok:
                    await self._private_client.connect()
                await self._restore_subscriptions()
                attempt = 0
            except Exception as exc:
                logger.debug("WebSocket reconnect failed: %s", exc)

    def _resolve_event_name(self, topic: str) -> str:
        if topic in _LEGACY_CHANNEL_ALIASES:
            return _LEGACY_CHANNEL_ALIASES[topic]
        if "." in topic:
            prefix = topic.split(".", 1)[0]
            if prefix in _LEGACY_CHANNEL_ALIASES:
                return _LEGACY_CHANNEL_ALIASES[prefix]
        return topic

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        topic = str(message.get("topic") or message.get("channel") or "")
        if topic:
            event_name = self._resolve_event_name(topic)
            await self.events.emit(event_name, message)
            await self.events.emit("market", message)

        for subscription in self._subscriptions:
            if subscription.callback is None:
                continue
            if topic and subscription.channel not in topic and topic not in subscription.channel:
                if not (
                    subscription.channel == "balance"
                    and topic == "contract.wallet"
                ):
                    continue
            result = subscription.callback(message)
            if asyncio.iscoroutine(result):
                await result

            legacy = self._resolve_event_name(topic) if topic else subscription.channel
            if legacy in {"order", "position", "wallet", "balance", "execution"}:
                await self.events.emit(legacy, message)
