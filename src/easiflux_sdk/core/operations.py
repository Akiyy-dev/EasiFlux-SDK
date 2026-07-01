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


def build_public_trades_params(
    *,
    symbol: str,
    limit: int | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["symbol"] = symbol
    if limit is not None:
        request_params["limit"] = limit
    return request_params


def build_funding_rate_history_params(
    *,
    symbol: str,
    from_time: int | None = None,
    to_time: int | None = None,
    limit: int | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["symbol"] = symbol
    if from_time is not None:
        request_params["from"] = from_time
    if to_time is not None:
        request_params["to"] = to_time
    if limit is not None:
        request_params["limit"] = limit
    return request_params


def build_instruments_params(
    *,
    symbol: str | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    if symbol is not None:
        request_params["symbol"] = symbol
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
    start_time: int | None = None,
    end_time: int | None = None,
    exec_type: str | None = None,
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
    if start_time is not None:
        request_params["start_time"] = start_time
    if end_time is not None:
        request_params["end_time"] = end_time
    if exec_type is not None:
        request_params["exec_type"] = exec_type
    return request_params


def build_transfer_history_params(
    *,
    start_time: int,
    end_time: int,
    coin: str | None = None,
    page_num: int | None = None,
    page_size: int | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["start_time"] = start_time
    request_params["end_time"] = end_time
    if coin is not None:
        request_params["coin"] = coin
    if page_num is not None:
        request_params["page_num"] = page_num
    if page_size is not None:
        request_params["page_size"] = page_size
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


def _payload_from_mapping_or_model(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(value, "to_api_payload"):
        return clean_mapping(value.to_api_payload())
    return clean_mapping(value)


def build_create_order_payload(order: Mapping[str, Any] | Any) -> dict[str, Any]:
    return _payload_from_mapping_or_model(order)


def build_cancel_order_payload(order_query: Mapping[str, Any] | Any) -> dict[str, Any]:
    return _payload_from_mapping_or_model(order_query)


def build_replace_order_payload(order: Mapping[str, Any] | Any) -> dict[str, Any]:
    return _payload_from_mapping_or_model(order)


def build_cancel_all_orders_payload(query: Mapping[str, Any] | Any) -> dict[str, Any]:
    return _payload_from_mapping_or_model(query)


def build_position_payload(payload: Mapping[str, Any] | Any) -> dict[str, Any]:
    return _payload_from_mapping_or_model(payload)
