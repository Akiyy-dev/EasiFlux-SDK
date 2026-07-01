from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .enums import OrderSide, OrderType, StopOrderType, TimeInForce, TriggerBy


def _optional_enum_value(value: object | None) -> object | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        return value.value
    return value


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    qty: str
    order_type: OrderType | None = None
    price: str | None = None
    position_idx: int | None = None
    time_in_force: TimeInForce | None = None
    order_link_id: str | None = None
    stop_order_type: StopOrderType | None = None
    trigger_by: TriggerBy | str | None = None
    trigger_price: str | None = None
    tp_trigger_by: TriggerBy | str | None = None
    take_profit: str | None = None
    sl_trigger_by: TriggerBy | str | None = None
    stop_loss: str | None = None
    reduce_only: bool | None = None
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "side": self.side.value,
            "qty": self.qty,
        }
        if self.order_type is not None:
            payload["order_type"] = self.order_type.value
        if self.price is not None:
            payload["price"] = self.price
        if self.position_idx is not None:
            payload["position_idx"] = self.position_idx
        if self.time_in_force is not None:
            payload["time_in_force"] = self.time_in_force.value
        if self.order_link_id is not None:
            payload["order_link_id"] = self.order_link_id
        if self.stop_order_type is not None:
            payload["stop_order_type"] = self.stop_order_type.value
        if self.trigger_by is not None:
            payload["trigger_by"] = _optional_enum_value(self.trigger_by)
        if self.trigger_price is not None:
            payload["trigger_price"] = self.trigger_price
        if self.tp_trigger_by is not None:
            payload["tp_trigger_by"] = _optional_enum_value(self.tp_trigger_by)
        if self.take_profit is not None:
            payload["take_profit"] = self.take_profit
        if self.sl_trigger_by is not None:
            payload["sl_trigger_by"] = _optional_enum_value(self.sl_trigger_by)
        if self.stop_loss is not None:
            payload["stop_loss"] = self.stop_loss
        if self.reduce_only is not None:
            payload["reduce_only"] = self.reduce_only
        if self.pz_link_id is not None:
            payload["pz_link_id"] = self.pz_link_id
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderRequest:
        return cls(
            symbol=str(data["symbol"]),
            side=OrderSide(data["side"]),
            qty=str(data["qty"]),
            order_type=OrderType(data["order_type"]) if data.get("order_type") else None,
            price=str(data["price"]) if data.get("price") is not None else None,
            position_idx=int(data["position_idx"]) if data.get("position_idx") is not None else None,
            time_in_force=TimeInForce(data["time_in_force"]) if data.get("time_in_force") else None,
            order_link_id=str(data["order_link_id"]) if data.get("order_link_id") else None,
            stop_order_type=StopOrderType(data["stop_order_type"]) if data.get("stop_order_type") else None,
            trigger_by=data.get("trigger_by"),
            trigger_price=str(data["trigger_price"]) if data.get("trigger_price") is not None else None,
            tp_trigger_by=data.get("tp_trigger_by"),
            take_profit=str(data["take_profit"]) if data.get("take_profit") is not None else None,
            sl_trigger_by=data.get("sl_trigger_by"),
            stop_loss=str(data["stop_loss"]) if data.get("stop_loss") is not None else None,
            reduce_only=bool(data["reduce_only"]) if data.get("reduce_only") is not None else None,
            pz_link_id=str(data["pz_link_id"]) if data.get("pz_link_id") else None,
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
class CancelAllOrdersRequest:
    symbol: str | None = None
    coin: str | None = None
    order_filter: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.coin is not None:
            payload["coin"] = self.coin
        if self.order_filter is not None:
            payload["order_filter"] = self.order_filter
        return payload


@dataclass
class ReplaceOrderRequest:
    symbol: str
    order_id: str | None = None
    order_link_id: str | None = None
    price: str | None = None
    qty: str | None = None
    trigger_price: str | None = None
    trigger_by: TriggerBy | str | None = None
    take_profit: str | None = None
    stop_loss: str | None = None
    tp_trigger_by: TriggerBy | str | None = None
    sl_trigger_by: TriggerBy | str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"symbol": self.symbol}
        if self.order_id is not None:
            payload["order_id"] = self.order_id
        if self.order_link_id is not None:
            payload["order_link_id"] = self.order_link_id
        if self.price is not None:
            payload["price"] = self.price
        if self.qty is not None:
            payload["qty"] = self.qty
        if self.trigger_price is not None:
            payload["trigger_price"] = self.trigger_price
        if self.trigger_by is not None:
            payload["trigger_by"] = _optional_enum_value(self.trigger_by)
        if self.take_profit is not None:
            payload["take_profit"] = self.take_profit
        if self.stop_loss is not None:
            payload["stop_loss"] = self.stop_loss
        if self.tp_trigger_by is not None:
            payload["tp_trigger_by"] = _optional_enum_value(self.tp_trigger_by)
        if self.sl_trigger_by is not None:
            payload["sl_trigger_by"] = _optional_enum_value(self.sl_trigger_by)
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
