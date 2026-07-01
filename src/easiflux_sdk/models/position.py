from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .enums import MarginMode, PositionMode, TpSlMode


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
    stop_loss: str | None = None
    tp_size: str | None = None
    sl_size: str | None = None
    tp_trigger_by: str | None = None
    sl_trigger_by: str | None = None
    pz_link_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        mode = self.tp_sl_mode.value if isinstance(self.tp_sl_mode, TpSlMode) else self.tp_sl_mode
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "position_idx": self.position_idx,
            "tp_sl_mode": mode,
        }
        optional_fields: dict[str, object | None] = {
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "tp_size": self.tp_size,
            "sl_size": self.sl_size,
            "tp_trigger_by": self.tp_trigger_by,
            "sl_trigger_by": self.sl_trigger_by,
            "pz_link_id": self.pz_link_id,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return payload


@dataclass
class ReplaceTpslRequest:
    symbol: str
    order_id: str
    take_profit: str | None = None
    stop_loss: str | None = None
    tp_size: str | None = None
    sl_size: str | None = None
    tp_trigger_by: str | None = None
    sl_trigger_by: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "order_id": self.order_id,
        }
        optional_fields: dict[str, object | None] = {
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "tp_size": self.tp_size,
            "sl_size": self.sl_size,
            "tp_trigger_by": self.tp_trigger_by,
            "sl_trigger_by": self.sl_trigger_by,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return payload


@dataclass
class SwitchMarginModeRequest:
    symbol: str
    margin_mode: MarginMode | str

    def to_api_payload(self) -> dict[str, Any]:
        mode = self.margin_mode.value if isinstance(self.margin_mode, MarginMode) else self.margin_mode
        return {"symbol": self.symbol, "margin_mode": mode}


@dataclass
class SwitchSeparatePositionModeRequest:
    coin: str
    position_mode: PositionMode | str

    def to_api_payload(self) -> dict[str, Any]:
        mode = self.position_mode.value if isinstance(self.position_mode, PositionMode) else self.position_mode
        return {"coin": self.coin, "position_mode": mode}
