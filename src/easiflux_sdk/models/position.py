from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .enums import MarginMode, PositionMode, TpSlMode, TriggerBy


def _optional_enum_value(value: object | None) -> object | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        return value.value
    return value


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


@dataclass
class SetLeverageRequest:
    symbol: str
    buy_leverage: int | None = None
    sell_leverage: int | None = None
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"symbol": self.symbol}
        if self.buy_leverage is not None:
            payload["buy_leverage"] = self.buy_leverage
        if self.sell_leverage is not None:
            payload["sell_leverage"] = self.sell_leverage
        if self.pz_link_id is not None:
            payload["pz_link_id"] = self.pz_link_id
        return payload


@dataclass
class AddMarginRequest:
    symbol: str
    position_idx: int
    margin: str
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "position_idx": self.position_idx,
            "margin": self.margin,
        }
        if self.pz_link_id is not None:
            payload["pz_link_id"] = self.pz_link_id
        return payload


@dataclass
class CloseAllPositionsRequest:
    symbol: str | None = None
    coin: str | None = None
    position_idx: int | None = None
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.coin is not None:
            payload["coin"] = self.coin
        if self.position_idx is not None:
            payload["position_idx"] = self.position_idx
        if self.pz_link_id is not None:
            payload["pz_link_id"] = self.pz_link_id
        return payload


@dataclass
class CreateTpslRequest:
    symbol: str
    position_idx: int
    tp_sl_mode: TpSlMode | str
    take_profit: str | None = None
    tp_size: str | None = None
    stop_loss: str | None = None
    sl_size: str | None = None
    tp_trigger_by: TriggerBy | str | None = None
    sl_trigger_by: TriggerBy | str | None = None
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "position_idx": self.position_idx,
            "tp_sl_mode": _optional_enum_value(self.tp_sl_mode),
        }
        if self.take_profit is not None:
            payload["take_profit"] = self.take_profit
        if self.tp_size is not None:
            payload["tp_size"] = self.tp_size
        if self.stop_loss is not None:
            payload["stop_loss"] = self.stop_loss
        if self.sl_size is not None:
            payload["sl_size"] = self.sl_size
        if self.tp_trigger_by is not None:
            payload["tp_trigger_by"] = _optional_enum_value(self.tp_trigger_by)
        if self.sl_trigger_by is not None:
            payload["sl_trigger_by"] = _optional_enum_value(self.sl_trigger_by)
        if self.pz_link_id is not None:
            payload["pz_link_id"] = self.pz_link_id
        return payload


@dataclass
class ReplaceTpslRequest:
    symbol: str
    order_id: str
    take_profit: str | None = None
    tp_size: str | None = None
    stop_loss: str | None = None
    sl_size: str | None = None
    tp_trigger_by: TriggerBy | str | None = None
    sl_trigger_by: TriggerBy | str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "order_id": self.order_id,
        }
        if self.take_profit is not None:
            payload["take_profit"] = self.take_profit
        if self.tp_size is not None:
            payload["tp_size"] = self.tp_size
        if self.stop_loss is not None:
            payload["stop_loss"] = self.stop_loss
        if self.sl_size is not None:
            payload["sl_size"] = self.sl_size
        if self.tp_trigger_by is not None:
            payload["tp_trigger_by"] = _optional_enum_value(self.tp_trigger_by)
        if self.sl_trigger_by is not None:
            payload["sl_trigger_by"] = _optional_enum_value(self.sl_trigger_by)
        return payload


@dataclass
class SwitchMarginModeRequest:
    symbol: str
    margin_mode: MarginMode | str

    def to_api_payload(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "margin_mode": _optional_enum_value(self.margin_mode),
        }


@dataclass
class SwitchSeparatePositionModeRequest:
    coin: str
    position_mode: PositionMode | str

    def to_api_payload(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "position_mode": _optional_enum_value(self.position_mode),
        }
