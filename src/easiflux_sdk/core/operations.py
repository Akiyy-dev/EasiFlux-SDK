from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .serialization import clean_mapping


def build_ticker_params(
    *,
    symbol: str | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    if symbol is not None:
        request_params["symbol"] = symbol
    return request_params


def build_kline_params(
    *,
    symbol: str,
    interval: str,
    limit: int | None = None,
    start: int | None = None,
    end: int | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params.update({"symbol": symbol, "interval": interval})
    if limit is not None:
        request_params["limit"] = limit
    if start is not None:
        request_params["start"] = start
    if end is not None:
        request_params["end"] = end
    if start_time is not None:
        request_params["start"] = start_time
    if end_time is not None:
        request_params["end"] = end_time
    return request_params


def build_depth_params(
    *,
    symbol: str,
    depth: int | None = None,
    limit: int | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["symbol"] = symbol
    if depth is not None:
        request_params["depth"] = depth
    if limit is not None:
        request_params["depth"] = limit
    return request_params


def build_order_query_params(
    *,
    symbol: str | None = None,
    coin: str | None = None,
    order_id: str | None = None,
    order_link_id: str | None = None,
    order_filter: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    if symbol is not None:
        request_params["symbol"] = symbol
    if coin is not None:
        request_params["coin"] = coin
    if order_id is not None:
        request_params["order_id"] = order_id
    if order_link_id is not None:
        request_params["order_link_id"] = order_link_id
    if order_filter is not None:
        request_params["order_filter"] = order_filter
    if limit is not None:
        request_params["limit"] = limit
    if cursor is not None:
        request_params["cursor"] = cursor
    return request_params


def build_fiat_rate_params(
    *,
    symbol_list: str | Sequence[str] | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    if symbol_list is not None:
        if isinstance(symbol_list, Sequence) and not isinstance(symbol_list, (str, bytes, bytearray)):
            request_params["symbol_list"] = ",".join(str(item) for item in symbol_list)
        else:
            request_params["symbol_list"] = symbol_list
    return request_params


def build_transfer_payload(
    *,
    amount: str,
    coin: str,
    from_wallet: str,
    to_wallet: str,
    extra_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "amount": amount,
        "coin": coin,
        "from_wallet": from_wallet,
        "to_wallet": to_wallet,
    }
    if extra_payload:
        payload.update(extra_payload)
    return payload


def build_create_order_payload(order: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(order, "to_api_payload"):
        return clean_mapping(order.to_api_payload())
    return clean_mapping(order)


def build_cancel_order_payload(order_query: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(order_query, "to_api_payload"):
        return clean_mapping(order_query.to_api_payload())
    return clean_mapping(order_query)
