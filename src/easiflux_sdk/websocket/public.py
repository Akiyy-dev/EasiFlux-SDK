from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

PUBLIC_TOPIC_PREFIXES = ("ob_snap_shot.", "candle.", "tickers-100.", "trades-100.")


def build_subscribe_message(*topics: str) -> dict[str, Any]:
    return {"op": "subscribe", "args": list(topics)}


def build_ping_message() -> dict[str, Any]:
    return {"op": "ping"}


def topic_ticker(symbol: str) -> str:
    return f"tickers-100.{symbol}"


def topic_depth(symbol: str, tick: int | str = 1) -> str:
    return f"ob_snap_shot.{symbol}.{tick}"


def topic_candle(symbol: str, interval: str) -> str:
    return f"candle.{interval}.{symbol}"


def topic_trades(symbol: str) -> str:
    return f"trades-100.{symbol}"


def resolve_public_topic(channel: str, params: dict[str, Any]) -> str:
    symbol = str(params.get("symbol", ""))
    if channel == "ticker":
        return topic_ticker(symbol)
    if channel == "depth":
        tick = params.get("tick", params.get("depth", 1))
        return topic_depth(symbol, tick)
    if channel == "candle":
        return topic_candle(symbol, str(params.get("interval", "1")))
    if channel == "trades":
        return topic_trades(symbol)
    if channel.startswith(PUBLIC_TOPIC_PREFIXES):
        return channel
    raise ValueError(f"Unsupported public channel: {channel}")


async def subscribe_public_topics(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    *topics: str,
) -> None:
    await send(build_subscribe_message(*topics))
