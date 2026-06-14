from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass
class Ticker:
    symbol: str | None = None
    last_price: str | None = None
    bid_price: str | None = None
    ask_price: str | None = None
    volume_24h: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Ticker:
        kwargs = {field.name: data.get(field.name) for field in fields(cls)}
        return cls(**kwargs)


@dataclass
class ServerTime:
    time_ms: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ServerTime | None:
        time_value = payload.get("time")
        if time_value is None and isinstance(payload.get("data"), dict):
            time_value = payload["data"].get("time")
        if time_value is None:
            return None
        return cls(time_ms=int(time_value))
