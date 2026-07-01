from __future__ import annotations

import pytest

from easiflux_sdk.config import AuthConfig, ResponseConfig
from easiflux_sdk.core.auth import Signer
from easiflux_sdk.core.events import EventEmitter
from easiflux_sdk.core.response_handler import ResponseHandler
from easiflux_sdk.core.time_sync import TimeSyncManager
from easiflux_sdk.websocket.manager import WebSocketManager
from easiflux_sdk.websocket.private import build_private_auth_message
from easiflux_sdk.websocket.public import (
    build_ping_message,
    build_subscribe_message,
    topic_candle,
    topic_depth,
    topic_ticker,
    topic_trades,
)
from easiflux_sdk.websocket.reconnect import ReconnectPolicy


def test_build_subscribe_message() -> None:
    message = build_subscribe_message("tickers-100.BTCUSDT")

    assert message == {"op": "subscribe", "args": ["tickers-100.BTCUSDT"]}


def test_topic_helpers() -> None:
    assert topic_ticker("BTCUSDT") == "tickers-100.BTCUSDT"
    assert topic_depth("BTCUSDT", 1) == "ob_snap_shot.BTCUSDT.1"
    assert topic_candle("BTCUSDT", "60") == "candle.60.BTCUSDT"
    assert topic_trades("BTCUSDT") == "trades-100.BTCUSDT"


def test_build_ping_message() -> None:
    assert build_ping_message() == {"op": "ping"}


def test_build_private_auth_message() -> None:
    handler = ResponseHandler(ResponseConfig())
    time_sync = TimeSyncManager(handler)
    signer = Signer("key", "secret", AuthConfig(), 5000, time_sync.get_timestamp)

    message = build_private_auth_message(signer=signer, expires_ms=1662350400000)

    assert message["op"] == "auth"
    assert message["args"][0] == "key"
    assert message["args"][1] == 1662350400000
    assert isinstance(message["args"][2], str)
    assert len(message["args"][2]) == 64


def test_reconnect_policy_backoff_caps_at_max() -> None:
    policy = ReconnectPolicy(backoff_factor=2.0, max_backoff=10.0)

    assert policy.backoff_delay(10) == 10.0
    assert policy.heartbeat_interval == 15.0


@pytest.mark.asyncio
async def test_websocket_manager_dispatches_topic_event() -> None:
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
