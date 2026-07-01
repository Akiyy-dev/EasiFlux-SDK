from __future__ import annotations

from enum import Enum


class OrderSide(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(str, Enum):
    LIMIT = "Limit"
    MARKET = "Market"


class TimeInForce(str, Enum):
    GOOD_TILL_CANCEL = "GoodTillCancel"
    IMMEDIATE_OR_CANCEL = "ImmediateOrCancel"
    FILL_OR_KILL = "FillOrKill"
    POST_ONLY = "PostOnly"


class StopOrderType(str, Enum):
    STOP = "Stop"


class TriggerBy(str, Enum):
    LAST_PRICE = "LastPrice"
    MARK_PRICE = "MarkPrice"


class ExecType(str, Enum):
    TRADE = "Trade"
    ADL_TRADE = "AdlTrade"
    FUNDING = "Funding"
    BUST_TRADE = "BustTrade"


class MarginMode(str, Enum):
    CROSS = "Cross"
    ISOLATED = "Isolated"


class PositionMode(str, Enum):
    SEPARATE = "Separate"
    MERGED = "Merged"


class TpSlMode(str, Enum):
    FULL = "Full"
    PARTIAL = "Partial"
