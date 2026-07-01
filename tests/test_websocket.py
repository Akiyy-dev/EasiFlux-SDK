from __future__ import annotations

import pytest

from easiflux_sdk.config import AuthConfig, ResponseConfig
from easiflux_sdk.core.auth import Signer
from easiflux_sdk.core.events import EventEmitter
from easiflux_sdk.core.response_handler import ResponseHandler
from easiflux_sdk.core.time_sync import TimeSyncManager
from easiflux_sdk.websocket.manager import WebSocketManager
from easiflux_sdk.websocket.private import build_private_auth_message, resolve_private_topic
from easiflux_sdk.websocket.public import (
    build_depth_topic,
    build_ping_message,
    build_public_subscribe_from_channel,
    build_public_subscribe_message,
    build_ticker_topic,
)
from easiflux_sdk.websocket.reconnect import ReconnectPolicy


def test_build_public_subscribe_message() -> None:
    message = build_public_subscribe_message(build_ticker_topic("BTCUSDT"))

    assert message == {"op": "subscribe", "args": ["tickers-100.BTCUSDT"]}


def test_build_public_subscribe_from_channel() -> None:
    message = build_public_subscribe_from_channel("depth", {"symbol": "BTCUSDT", "tick": 1})

    assert message["args"] == [build_depth_topic("BTCUSDT", tick=1)]


def test_build_ping_message() -> None:
    assert build_ping_message() == {"op": "ping"}


def test_build_private_auth_message() -> None:
    signer = Signer("key", "secret", AuthConfig(), 5000, lambda: 1)
    message = build_private_auth_message(signer=signer, expires_ms=1234567890)

    assert message["op"] == "auth"
    assert message["args"][0] == "key"
    assert message["args"][1] == 1234567890
    assert isinstance(message["args"][2], str)


def test_resolve_private_topic_aliases_balance() -> None:
    assert resolve_private_topic("balance") == "contract.wallet"


def test_reconnect_policy_backoff_caps_at_max() -> None:
    policy = ReconnectPolicy(backoff_factor=2.0, max_backoff=10.0)

    assert policy.backoff_delay(10) == 10.0


@pytest.mark.asyncio
async def test_websocket_manager_dispatches_event() -> None:
    events = EventEmitter()
    received: list[str] = []

    @events.on("ticker")
    async def on_ticker(_: dict) -> None:
        received.append("ticker")

    handler = ResponseHandler(ResponseConfig())
    time_sync = TimeSyncManager(handler)
    signer = Signer("key", "secret", AuthConfig(), 5000, time_sync.get_timestamp)
    manager = WebSocketManager(
        ws_public_url="wss://example.test/public",
        ws_private_url="wss://example.test/private",
        api_key="key",
        api_secret="secret",
        auth_config=AuthConfig(),
        signer=signer,
        time_sync=time_sync,
        events=events,
    )

    await manager._dispatch_message({"topic": "tickers-100.BTCUSDT", "data": {"s": "BTCUSDT"}})

    assert received == ["ticker"]
