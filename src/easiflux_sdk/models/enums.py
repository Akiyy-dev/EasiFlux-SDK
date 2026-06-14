from __future__ import annotations

from enum import StrEnum


class OrderSide(StrEnum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(StrEnum):
    LIMIT = "Limit"
    MARKET = "Market"


class TimeInForce(StrEnum):
    GOOD_TILL_CANCEL = "GoodTillCancel"
    IMMEDIATE_OR_CANCEL = "ImmediateOrCancel"
    FILL_OR_KILL = "FillOrKill"
