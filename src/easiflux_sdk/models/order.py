from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .enums import OrderSide, OrderType, TimeInForce


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    order_type: OrderType
    qty: str
    price: str | None = None
    position_idx: int | None = None
    time_in_force: TimeInForce | None = None
    order_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "qty": self.qty,
        }
        if self.price is not None:
            payload["price"] = self.price
        if self.position_idx is not None:
            payload["position_idx"] = self.position_idx
        if self.time_in_force is not None:
            payload["time_in_force"] = self.time_in_force.value
        if self.order_link_id is not None:
            payload["order_link_id"] = self.order_link_id
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderRequest:
        return cls(
            symbol=str(data["symbol"]),
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            qty=str(data["qty"]),
            price=str(data["price"]) if data.get("price") is not None else None,
            position_idx=int(data["position_idx"]) if data.get("position_idx") is not None else None,
            time_in_force=TimeInForce(data["time_in_force"]) if data.get("time_in_force") else None,
            order_link_id=str(data["order_link_id"]) if data.get("order_link_id") else None,
        )


@dataclass
class CancelOrderRequest:
    symbol: str
    order_id: str | None = None
    order_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"symbol": self.symbol}
        if self.order_id is not None:
            payload["order_id"] = self.order_id
        if self.order_link_id is not None:
            payload["order_link_id"] = self.order_link_id
        return payload


@dataclass
class Order:
    order_id: str | None = None
    order_link_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    order_type: str | None = None
    price: str | None = None
    qty: str | None = None
    status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Order:
        kwargs = {field.name: data.get(field.name) for field in fields(cls)}
        return cls(**kwargs)
