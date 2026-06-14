from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass
class Position:
    symbol: str | None = None
    side: str | None = None
    size: str | None = None
    entry_price: str | None = None
    leverage: str | None = None
    unrealised_pnl: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Position:
        kwargs = {field.name: data.get(field.name) for field in fields(cls)}
        return cls(**kwargs)
