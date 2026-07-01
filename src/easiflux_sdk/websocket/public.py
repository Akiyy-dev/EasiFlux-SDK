from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

PUBLIC_TOPICS = frozenset({"ticker", "depth", "candle", "trades"})

PRIVATE_TOPICS = frozenset({"position", "order", "execution", "wallet", "balance"})

_TOPIC_ALIASES = {
    "ticker": "tickers",
    "depth": "ob_snap_shot",
    "trades": "trades",
    "balance": "wallet",
}


def build_ticker_topic(symbol: str) -> str:
    return f"tickers-100.{symbol}"


def build_depth_topic(symbol: str, *, tick: int | str = 1) -> str:
    return f"ob_snap_shot.{symbol}.{tick}"


def build_candle_topic(symbol: str, interval: str) -> str:
    return f"candle.{interval}.{symbol}"


def build_trades_topic(symbol: str) -> str:
    return f"trades-100.{symbol}"


def build_public_subscribe_message(*topics: str) -> dict[str, Any]:
    return {"op": "subscribe", "args": list(topics)}


def build_public_subscribe_from_channel(channel: str, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol", ""))
    if channel == "ticker":
        return build_public_subscribe_message(build_ticker_topic(symbol))
    if channel == "depth":
        tick = params.get("tick", params.get("depth", 1))
        return build_public_subscribe_message(build_depth_topic(symbol, tick=tick))
    if channel == "candle":
        interval = str(params.get("interval", "1"))
        return build_public_subscribe_message(build_candle_topic(symbol, interval))
    if channel == "trades":
        return build_public_subscribe_message(build_trades_topic(symbol))
    raise ValueError(f"Unsupported public channel: {channel}")


async def subscribe_public(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    channel: str,
    params: dict[str, Any],
) -> None:
    if channel not in PUBLIC_TOPICS:
        raise ValueError(f"Unsupported public channel: {channel}")
    await send(build_public_subscribe_from_channel(channel, params))


def build_ping_message() -> dict[str, Any]:
    return {"op": "ping"}
