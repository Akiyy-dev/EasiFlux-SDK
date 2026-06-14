from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ..core.auth import Signer
from ..core.time_sync import TimeSyncManager

PRIVATE_CHANNELS = {"order", "position", "balance"}


def build_private_auth_message(
    *,
    signer: Signer,
    time_sync: TimeSyncManager,
) -> dict[str, Any]:
    timestamp = str(time_sync.get_timestamp())
    signature = signer.sign(f"{timestamp}{signer.api_key}")
    return {
        "op": "auth",
        "args": {
            "api_key": signer.api_key,
            "timestamp": timestamp,
            "sign": signature,
        },
    }


def build_private_subscribe_message(channel: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "op": "subscribe",
        "channel": channel,
        "args": params or {},
    }


async def authenticate_private(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    *,
    signer: Signer,
    time_sync: TimeSyncManager,
) -> None:
    signer.ensure_credentials()
    await send(build_private_auth_message(signer=signer, time_sync=time_sync))


async def subscribe_private(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    channel: str,
    params: dict[str, Any] | None = None,
) -> None:
    if channel not in PRIVATE_CHANNELS:
        raise ValueError(f"Unsupported private channel: {channel}")
    await send(build_private_subscribe_message(channel, params))
