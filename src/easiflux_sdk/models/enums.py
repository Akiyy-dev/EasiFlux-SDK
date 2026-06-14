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
