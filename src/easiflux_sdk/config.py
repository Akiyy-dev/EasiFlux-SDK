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
    "public_trades": "/futures/public/v1/market/trades",
    "funding_rate_history": "/futures/public/v1/market/funding-rate-history",
    "mark_price_kline": "/futures/public/v1/market/mark-price-kline",
    "instruments": "/futures/public/v1/instruments",
    "risk_limit": "/futures/public/v1/position-risk-limit",
    "market_close_time": "/futures/public/v1/market/market-close-time",
    "create_order": "/futures/private/v1/create-order",
    "cancel_order": "/futures/private/v1/cancel-order",
    "cancel_all_orders": "/futures/private/v1/cancel-all-orders",
    "replace_order": "/futures/private/v1/replace-order",
    "order": "/futures/private/v1/trade/activity-orders",
    "orders": "/futures/private/v1/trade/orders",
    "trade_fills": "/futures/private/v1/trade/fills",
    "balances": "/futures/private/v1/account/balance",
    "positions": "/futures/private/v1/position/list",
    "fee_rate": "/futures/private/v1/account/fee-rate",
    "set_leverage": "/futures/private/v1/position/set-leverage",
    "add_margin": "/futures/private/v1/position/add-margin",
    "close_all_positions": "/futures/private/v1/position/close-all",
    "closed_pnl": "/futures/private/v1/position/closed-pnl",
    "create_tpsl": "/futures/private/v1/position/create-tpsl",
    "replace_tpsl": "/futures/private/v1/position/replace-tpsl",
    "switch_margin_mode": "/futures/private/v1/position/switch-margin-mode",
    "switch_separate_position_mode": "/futures/private/v1/position/switch-separate-mode",
    "funding_balances": "/asset-api/account/private/v1/get-funding-account-balance",
    "funding_transfer": "/asset-api/account/private/v1/user-account-transfer",
    "user_id": "/asset-api/account/private/v1/userid",
    "transfer_history": "/asset-api/account/private/v1/user-transfer-rercord/page",
    "fiat_rate": "/asset-api/fiat/public/v1/rate",
}

DEFAULT_WS_URLS: dict[str, str] = {
    "contract_public": "wss://ws.easicoin.io/contract/public/v1",
    "contract_private": "wss://ws.easicoin.io/contract/private/v1",
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
