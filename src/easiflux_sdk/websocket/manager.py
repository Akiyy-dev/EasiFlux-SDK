from __future__ import annotations

import asyncio
import warnings
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..config import AuthConfig
from ..core.auth import Signer
from ..core.events import EventEmitter
from ..core.logging import get_logger
from ..core.time_sync import TimeSyncManager
from .client import WebSocketClient
from .private import (
    LEGACY_PRIVATE_CHANNELS,
    authenticate_private,
    resolve_private_topic,
    subscribe_private_topics,
)
from .public import build_ping_message, resolve_public_topic, subscribe_public_topics
from .reconnect import ReconnectPolicy

logger = get_logger(__name__)

Callback = Callable[[dict[str, Any]], Awaitable[None] | None]

TOPIC_EVENT_ALIASES: dict[str, str] = {
    "tickers-100": "ticker",
    "ob_snap_shot": "depth",
    "trades-100": "trades",
    "candle": "candle",
    "contract.position": "position",
    "contract.order": "order",
    "contract.execution": "execution",
    "contract.wallet": "balance",
}


@dataclass
class Subscription:
    topic: str
    callback: Callback | None = None
    private: bool = False


class WebSocketManager:
    def __init__(
        self,
        *,
        ws_public_url: str,
        ws_private_url: str,
        api_key: str,
        api_secret: str,
        auth_config: AuthConfig,
        signer: Signer,
        time_sync: TimeSyncManager,
        events: EventEmitter,
        reconnect_policy: ReconnectPolicy | None = None,
    ) -> None:
        self.ws_public_url = ws_public_url
        self.ws_private_url = ws_private_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.auth_config = auth_config
        self.signer = signer
        self.time_sync = time_sync
        self.events = events
        self.reconnect_policy = reconnect_policy or ReconnectPolicy()

        self._public_client = WebSocketClient(ws_public_url)
        self._private_client = WebSocketClient(ws_private_url)
        self._subscriptions: list[Subscription] = []
        self._private_authenticated = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._public_client.add_handler(self._dispatch_message)
        self._private_client.add_handler(self._dispatch_message)

    async def connect(self) -> None:
        await self._public_client.connect()
        if self._has_private_subscriptions():
            await self._private_client.connect()
            await self._authenticate_private()
        self._monitor_task = asyncio.create_task(self._monitor_connection())
        await self._restore_subscriptions()

    async def subscribe(
        self,
        channel: str,
        params: dict[str, Any] | None = None,
        *,
        callback: Callback | None = None,
    ) -> None:
        """Subscribe using a topic string or legacy channel name."""
        params = params or {}
        if channel.startswith(("contract.", "tickers-100.", "ob_snap_shot.", "candle.", "trades-100.")):
            topic = channel
            private = topic.startswith("contract.")
        else:
            warnings.warn(
                f"Channel-based subscribe('{channel}') is deprecated; pass the official topic string instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if channel in LEGACY_PRIVATE_CHANNELS or channel in {"position", "order", "execution", "balance"}:
                topic = resolve_private_topic(channel, params)
                private = True
            else:
                topic = resolve_public_topic(channel, params)
                private = False

        await self.subscribe_topic(topic, callback=callback, private=private)

    async def subscribe_topic(
        self,
        topic: str,
        *,
        callback: Callback | None = None,
        private: bool | None = None,
    ) -> None:
        is_private = private if private is not None else topic.startswith("contract.")
        subscription = Subscription(topic=topic, callback=callback, private=is_private)
        self._subscriptions.append(subscription)

        if is_private and not self._private_client.connected:
            await self._private_client.connect()
            await self._authenticate_private()
        elif not is_private and not self._public_client.connected:
            await self.connect()
            return

        await self._apply_subscription(subscription)

    async def subscribe_ticker(self, symbol: str, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic(f"tickers-100.{symbol}", callback=callback, private=False)

    async def subscribe_depth(
        self,
        symbol: str,
        *,
        tick: int | str = 1,
        callback: Callback | None = None,
    ) -> None:
        await self.subscribe_topic(f"ob_snap_shot.{symbol}.{tick}", callback=callback, private=False)

    async def subscribe_candle(
        self,
        symbol: str,
        interval: str,
        *,
        callback: Callback | None = None,
    ) -> None:
        await self.subscribe_topic(f"candle.{interval}.{symbol}", callback=callback, private=False)

    async def subscribe_trades(self, symbol: str, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic(f"trades-100.{symbol}", callback=callback, private=False)

    async def subscribe_position(self, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic("contract.position", callback=callback, private=True)

    async def subscribe_order(self, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic("contract.order", callback=callback, private=True)

    async def subscribe_execution(self, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic("contract.execution", callback=callback, private=True)

    async def subscribe_wallet(self, *, callback: Callback | None = None) -> None:
        await self.subscribe_topic("contract.wallet", callback=callback, private=True)

    async def close(self) -> None:
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await self._public_client.close()
        await self._private_client.close()

    def _has_private_subscriptions(self) -> bool:
        return any(subscription.private for subscription in self._subscriptions)

    async def _authenticate_private(self) -> None:
        await authenticate_private(self._private_client.send, signer=self.signer)
        self._private_authenticated = True

    async def _apply_subscription(self, subscription: Subscription) -> None:
        if subscription.private:
            if not self._private_authenticated:
                await self._authenticate_private()
            await subscribe_private_topics(self._private_client.send, subscription.topic)
        else:
            await subscribe_public_topics(self._public_client.send, subscription.topic)

    async def _restore_subscriptions(self) -> None:
        self._private_authenticated = False
        public_topics = [s.topic for s in self._subscriptions if not s.private]
        private_topics = [s.topic for s in self._subscriptions if s.private]

        if public_topics and self._public_client.connected:
            await subscribe_public_topics(self._public_client.send, *public_topics)
        if private_topics:
            if not self._private_client.connected:
                await self._private_client.connect()
            await self._authenticate_private()
            await subscribe_private_topics(self._private_client.send, *private_topics)

    async def _send_heartbeats(self) -> None:
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
            if self._public_client.connected or self._private_client.connected:
                await self._send_heartbeats()
                attempt = 0

            public_ok = self._public_client.connected or not any(not s.private for s in self._subscriptions)
            private_ok = self._private_client.connected or not self._has_private_subscriptions()
            if public_ok and private_ok:
                continue

            if attempt >= self.reconnect_policy.max_retries:
                logger.debug("WebSocket reconnect attempts exhausted")
                return

            delay = self.reconnect_policy.backoff_delay(attempt)
            logger.debug("WebSocket reconnecting in %.1fs (attempt %s)", delay, attempt + 1)
            await asyncio.sleep(delay)
            attempt += 1

            try:
                if not self._public_client.connected and any(not s.private for s in self._subscriptions):
                    await self._public_client.connect()
                if self._has_private_subscriptions() and not self._private_client.connected:
                    await self._private_client.connect()
                await self._restore_subscriptions()
                attempt = 0
            except Exception as exc:
                logger.debug("WebSocket reconnect failed: %s", exc)

    def _event_name_for_topic(self, topic: str) -> str:
        if topic in TOPIC_EVENT_ALIASES:
            return TOPIC_EVENT_ALIASES[topic]
        if "." in topic:
            prefix = topic.split(".", 1)[0]
            if prefix in TOPIC_EVENT_ALIASES:
                return TOPIC_EVENT_ALIASES[prefix]
        return topic

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        topic = str(message.get("topic") or message.get("channel") or "")
        if topic:
            event_name = self._event_name_for_topic(topic)
            await self.events.emit(event_name, message)
            await self.events.emit("market", message)

        for subscription in self._subscriptions:
            if subscription.callback is None:
                continue
            if topic and subscription.topic not in topic:
                continue
            result = subscription.callback(message)
            if asyncio.iscoroutine(result):
                await result

            if subscription.private:
                alias = self._event_name_for_topic(subscription.topic)
                await self.events.emit(alias, message)
