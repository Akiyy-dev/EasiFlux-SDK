from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TimestampUnit = Literal["ms", "s"]
SignatureEncoding = Literal["hex", "base64"]

DEFAULT_ENDPOINTS: dict[str, str] = {
    "server_time": "/futures/public/v1/market/time",
    "ticker": "/futures/public/v1/market/tickers",
    "kline": "/futures/public/v1/market/kline",
    "depth": "/futures/public/v1/market/order-book",
    "create_order": "/futures/private/v1/create-order",
    "cancel_order": "/futures/private/v1/cancel-order",
    "order": "/futures/private/v1/trade/activity-orders",
    "orders": "/futures/private/v1/trade/orders",
    "balances": "/futures/private/v1/account/balance",
    "positions": "/futures/private/v1/position/list",
    "fee_rate": "/futures/private/v1/account/fee-rate",
    "funding_balances": "/asset-api/account/private/v1/get-funding-account-balance",
    "funding_transfer": "/asset-api/account/private/v1/user-account-transfer",
    "fiat_rate": "/asset-api/fiat/public/v1/rate",
}


@dataclass(slots=True)
class AuthConfig:
    api_key_header: str = "Access-Key"
    signature_header: str = "Access-Sign"
    timestamp_header: str = "Access-Timestamp"
    recv_window_header: str = "Recv-Window"
    content_type: str = "application/json"
    timestamp_unit: TimestampUnit = "ms"
    signature_algorithm: str = "HMAC-SHA256"
    signature_encoding: SignatureEncoding = "hex"
    sort_query_for_signature: bool = False


@dataclass(slots=True)
class ResponseConfig:
    code_fields: tuple[str, ...] = ("code", "errorCode", "status")
    success_codes: tuple[object, ...] = (0, "0", 200, "200", "SUCCESS", "success")
    success_field: str | None = None
    success_values: tuple[object, ...] = (True, "true", 1, "1")
    message_fields: tuple[str, ...] = (
        "msg",
        "message",
        "error",
        "detail",
        "errorMessage",
    )
