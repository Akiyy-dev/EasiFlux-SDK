from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass
class Balance:
    coin: str | None = None
    equity: str | None = None
    wallet_balance: str | None = None
    available_balance: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Balance:
        kwargs = {field.name: data.get(field.name) for field in fields(cls)}
        return cls(**kwargs)


@dataclass
class TransferRequest:
    amount: str
    coin: str
    from_wallet: str
    to_wallet: str

    def to_api_payload(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "coin": self.coin,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
        }
