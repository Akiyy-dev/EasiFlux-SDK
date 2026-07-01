from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from ..core.auth import Signer

PRIVATE_TOPICS = {
    "contract.position",
    "contract.order",
    "contract.execution",
    "contract.wallet",
}

# Legacy channel names mapped to official topics.
LEGACY_PRIVATE_CHANNELS = {
    "position": "contract.position",
    "order": "contract.order",
    "execution": "contract.execution",
    "balance": "contract.wallet",
}


def build_private_auth_message(*, signer: Signer, expires_ms: int | None = None) -> dict[str, Any]:
    signer.ensure_credentials()
    expires = expires_ms if expires_ms is not None else int((time.time() + 60) * 1000)
    signature = signer.sign_ws_auth(expires)
    return {
        "op": "auth",
        "args": [signer.api_key, expires, signature],
    }


def resolve_private_topic(channel: str, _params: dict[str, Any] | None = None) -> str:
    if channel in PRIVATE_TOPICS:
        return channel
    if channel in LEGACY_PRIVATE_CHANNELS:
        return LEGACY_PRIVATE_CHANNELS[channel]
    raise ValueError(f"Unsupported private channel: {channel}")


async def authenticate_private(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    *,
    signer: Signer,
) -> None:
    await send(build_private_auth_message(signer=signer))


async def subscribe_private_topics(
    send: Callable[[dict[str, Any]], Awaitable[None]],
    *topics: str,
) -> None:
    await send({"op": "subscribe", "args": list(topics)})
