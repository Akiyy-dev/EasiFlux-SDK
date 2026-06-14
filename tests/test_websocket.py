from __future__ import annotations

import pytest

from easiflux_sdk.config import AuthConfig, ResponseConfig
from easiflux_sdk.core.auth import Signer
from easiflux_sdk.core.events import EventEmitter
from easiflux_sdk.core.response_handler import ResponseHandler
from easiflux_sdk.core.time_sync import TimeSyncManager
from easiflux_sdk.websocket.manager import WebSocketManager
from easiflux_sdk.websocket.public import build_public_subscribe_message
from easiflux_sdk.websocket.reconnect import ReconnectPolicy


def test_build_public_subscribe_message() -> None:
    message = build_public_subscribe_message("ticker", {"symbol": "BTCUSDT"})

    assert message["op"] == "subscribe"
    assert message["channel"] == "ticker"
    assert message["args"]["symbol"] == "BTCUSDT"


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
        ws_url="wss://example.test/ws",
        api_key="key",
        api_secret="secret",
        auth_config=AuthConfig(),
        signer=signer,
        time_sync=time_sync,
        events=events,
    )

    await manager._dispatch_message({"channel": "ticker", "data": {"symbol": "BTCUSDT"}})

    assert received == ["ticker"]
