from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from ..core.auth import Signer

PRIVATE_TOPICS = frozenset({"position", "order", "execution", "wallet", "balance"})

_PRIVATE_TOPIC_MAP = {
    "position": "contract.position",
    "order": "contract.order",
    "execution": "contract.execution",
    "wallet": "contract.wallet",
    "balance": "contract.wallet",
}


def build_private_auth_message(*, signer: Signer, expires_ms: int | None = None) -> dict[str, Any]:
    expires = expires_ms if expires_ms is not None else int((time.time() + 60) * 1000)
    signature = signer.sign_ws_auth(expires)
    return {
        "op": "auth",
        "args": [signer.api_key, expires, signature],
    }


def build_private_subscribe_message(*topics: str) -> dict[str, Any]:
    return {"op": "subscribe", "args": list(topics)}


def resolve_private_topic(channel: str) -> str:
    if channel in _PRIVATE_TOPIC_MAP:
        return _PRIVATE_TOPIC_MAP[channel]
    if channel.startswith("contract."):
        return channel
    raise ValueError(f"Unsupported private channel: {channel}")


def build_private_subscribe_from_channel(channel: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    del params
    return build_private_subscribe_message(resolve_private_topic(channel))


async def authenticate_private(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    *,
    signer: Signer,
) -> None:
    signer.ensure_credentials()
    await send(build_private_auth_message(signer=signer))


async def subscribe_private(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    channel: str,
    params: dict[str, Any] | None = None,
) -> None:
    if channel not in PRIVATE_TOPICS and not channel.startswith("contract."):
        raise ValueError(f"Unsupported private channel: {channel}")
    await send(build_private_subscribe_from_channel(channel, params))
