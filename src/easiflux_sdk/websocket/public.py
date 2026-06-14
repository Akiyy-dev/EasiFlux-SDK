from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

PUBLIC_CHANNELS = {"ticker", "depth", "trades"}


def build_public_subscribe_message(channel: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "op": "subscribe",
        "channel": channel,
        "args": params,
    }


async def subscribe_public(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    channel: str,
    params: dict[str, Any],
) -> None:
    if channel not in PUBLIC_CHANNELS:
        raise ValueError(f"Unsupported public channel: {channel}")
    await send(build_public_subscribe_message(channel, params))
