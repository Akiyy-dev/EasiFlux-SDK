from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin

from requests import Session

from .config import DEFAULT_ENDPOINTS, AuthConfig, ResponseConfig
from .core.auth import Signer
from .core.operations import (
    build_cancel_all_orders_payload,
    build_cancel_order_payload,
    build_create_order_payload,
    build_depth_params,
    build_fiat_rate_params,
    build_funding_rate_history_params,
    build_instruments_params,
    build_kline_params,
    build_order_query_params,
    build_position_payload,
    build_public_trades_params,
    build_replace_order_payload,
    build_ticker_params,
    build_transfer_history_params,
    build_transfer_payload,
)
from .core.response_handler import ResponseHandler
from .core.serialization import clean_mapping, serialize_json_body
from .core.time_sync import TimeSyncManager
from .exceptions import APIError, ConfigurationError
from .response import SDKResponse
from .transport.sync import RequestsTransport


class EasiFluxSDK:
    """Synchronous SDK for the official EasiCoin REST API."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        base_url: str = "https://api.easicoin.io",
        *,
        endpoint_map: Mapping[str, str] | None = None,
        auth_config: AuthConfig | None = None,
        response_config: ResponseConfig | None = None,
        timeout: float = 10.0,
        recv_window: int | None = 5000,
        user_agent: str = "EasiFluxSDK/0.3.0",
        auto_sync_time: bool = True,
        time_sync_interval: float = 30.0,
        sync_on_init: bool = True,
        response_typed: bool = False,
        session: Session | None = None,
        transport: RequestsTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.user_agent = user_agent
        self.auto_sync_time = auto_sync_time
        self.time_sync_interval = time_sync_interval
        self.sync_on_init = sync_on_init
        self.response_typed = response_typed

        self.auth_config = auth_config or AuthConfig()
        self.response_config = response_config or ResponseConfig()
        self.endpoint_map: dict[str, str] = dict(DEFAULT_ENDPOINTS)
        if endpoint_map:
            self.endpoint_map.update(endpoint_map)

        self._response_handler = ResponseHandler(self.response_config)
        self._time_sync = TimeSyncManager(
            self._response_handler,
            enabled=auto_sync_time,
            interval=time_sync_interval,
            sync_on_init=sync_on_init,
            timestamp_unit=self.auth_config.timestamp_unit,
        )
        self._signer = Signer(
            self.api_key,
            self.api_secret,
            self.auth_config,
            self.recv_window,
            self._time_sync.get_timestamp,
        )
        self._transport = transport or RequestsTransport(session=session)

        if self.auto_sync_time and self.sync_on_init:
            self.sync_time(force=True)

    @property
    def session(self) -> Session:
        return self._transport._session

    @property
    def server_time_offset_ms(self) -> int:
        return self._time_sync.server_time_offset_ms

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> EasiFluxSDK:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def set_endpoint(self, name: str, path: str) -> None:
        self.endpoint_map[name] = path

    def get_server_time(self, *, path: str | None = None) -> Any:
        return self._request("GET", self._resolve_endpoint("server_time", path))

    def sync_time(self, *, force: bool = False) -> int:
        return self._time_sync.sync(self.get_server_time, force=force)

    def get_ticker(
        self,
        symbol: str | None = None,
        *,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_ticker_params(symbol=symbol, params=params)
        return self._request("GET", self._resolve_endpoint("ticker", path), params=request_params)

    def get_kline(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int | None = None,
        start: int | None = None,
        end: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_kline_params(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start=start,
            end=end,
            start_time=start_time,
            end_time=end_time,
            params=params,
        )
        return self._request("GET", self._resolve_endpoint("kline", path), params=request_params)

    def get_depth(
        self,
        symbol: str,
        *,
        depth: int | None = None,
        limit: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_depth_params(symbol=symbol, depth=depth, limit=limit, params=params)
        return self._request("GET", self._resolve_endpoint("depth", path), params=request_params)

    def get_public_trades(
        self,
        symbol: str,
        *,
        limit: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_public_trades_params(symbol=symbol, limit=limit, params=params)
        return self._request("GET", self._resolve_endpoint("public_trades", path), params=request_params)

    def get_funding_rate_history(
        self,
        symbol: str,
        *,
        from_time: int | None = None,
        to_time: int | None = None,
        limit: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_funding_rate_history_params(
            symbol=symbol,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
            params=params,
        )
        return self._request(
            "GET",
            self._resolve_endpoint("funding_rate_history", path),
            params=request_params,
        )

    def get_mark_price_kline(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int | None = None,
        start: int | None = None,
        end: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_kline_params(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start=start,
            end=end,
            params=params,
        )
        return self._request(
            "GET",
            self._resolve_endpoint("mark_price_kline", path),
            params=request_params,
        )

    def get_instruments(
        self,
        *,
        symbol: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_instruments_params(symbol=symbol, params=params)
        return self._request("GET", self._resolve_endpoint("instruments", path), params=request_params)

    def get_risk_limit(
        self,
        symbol: str,
        *,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_ticker_params(symbol=symbol, params=params)
        return self._request("GET", self._resolve_endpoint("risk_limit", path), params=request_params)

    def get_market_close_time(self, *, path: str | None = None) -> Any:
        return self._request("GET", self._resolve_endpoint("market_close_time", path))

    def get_trading_fee_rate(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(symbol=symbol, coin=coin, params=params)
        return self._signed_request("GET", self._resolve_endpoint("fee_rate", path), params=request_params)

    def create_order(
        self,
        order: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        payload = build_create_order_payload(order)
        return self._private_write(
            "POST",
            self._resolve_endpoint("create_order", path),
            payload=payload,
            use_json=use_json,
        )

    def cancel_order(
        self,
        order_query: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        payload = build_cancel_order_payload(order_query)
        return self._private_write(
            "POST",
            self._resolve_endpoint("cancel_order", path),
            payload=payload,
            use_json=use_json,
        )

    def cancel_all_orders(
        self,
        order_query: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        payload = build_cancel_all_orders_payload(order_query)
        return self._private_write(
            "POST",
            self._resolve_endpoint("cancel_all_orders", path),
            payload=payload,
            use_json=use_json,
        )

    def replace_order(
        self,
        order: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        payload = build_replace_order_payload(order)
        return self._private_write(
            "POST",
            self._resolve_endpoint("replace_order", path),
            payload=payload,
            use_json=use_json,
        )

    def get_order(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        order_id: str | None = None,
        order_link_id: str | None = None,
        order_filter: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(
            symbol=symbol,
            coin=coin,
            order_id=order_id,
            order_link_id=order_link_id,
            order_filter=order_filter,
            limit=limit,
            cursor=cursor,
            params=params,
        )
        return self._signed_request(
            "GET",
            self._resolve_endpoint("order", path),
            params=request_params,
        )

    def get_open_orders(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        order_id: str | None = None,
        order_link_id: str | None = None,
        order_filter: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.get_order(
            symbol=symbol,
            coin=coin,
            order_id=order_id,
            order_link_id=order_link_id,
            order_filter=order_filter,
            limit=limit,
            cursor=cursor,
            path=path,
            params=params,
        )

    def get_orders(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        order_id: str | None = None,
        order_link_id: str | None = None,
        order_filter: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(
            symbol=symbol,
            coin=coin,
            order_id=order_id,
            order_link_id=order_link_id,
            order_filter=order_filter,
            limit=limit,
            cursor=cursor,
            params=params,
        )
        return self._signed_request(
            "GET",
            self._resolve_endpoint("orders", path),
            params=request_params,
        )

    def get_trade_fills(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        order_id: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        exec_type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(
            symbol=symbol,
            coin=coin,
            order_id=order_id,
            start_time=start_time,
            end_time=end_time,
            exec_type=exec_type,
            limit=limit,
            cursor=cursor,
            params=params,
        )
        return self._signed_request(
            "GET",
            self._resolve_endpoint("trade_fills", path),
            params=request_params,
        )

    def get_balances(
        self,
        *,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(coin=coin, params=params)
        return self._signed_request(
            "GET",
            self._resolve_endpoint("balances", path),
            params=request_params,
        )

    def get_positions(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(symbol=symbol, coin=coin, params=params)
        return self._signed_request(
            "GET",
            self._resolve_endpoint("positions", path),
            params=request_params,
        )

    def set_leverage(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("set_leverage", path),
            payload=body,
            use_json=use_json,
        )

    def add_margin(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("add_margin", path),
            payload=body,
            use_json=use_json,
        )

    def close_all_positions(
        self,
        payload: Mapping[str, Any] | Any | None = None,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload or {})
        return self._private_write(
            "POST",
            self._resolve_endpoint("close_all_positions", path),
            payload=body,
            use_json=use_json,
        )

    def get_closed_pnl(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        start_time: str | int | None = None,
        end_time: str | int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_order_query_params(
            symbol=symbol,
            coin=coin,
            limit=limit,
            cursor=cursor,
            params=params,
        )
        if start_time is not None:
            request_params["start_time"] = start_time
        if end_time is not None:
            request_params["end_time"] = end_time
        return self._signed_request(
            "GET",
            self._resolve_endpoint("closed_pnl", path),
            params=request_params,
        )

    def create_tpsl(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("create_tpsl", path),
            payload=body,
            use_json=use_json,
        )

    def replace_tpsl(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("replace_tpsl", path),
            payload=body,
            use_json=use_json,
        )

    def switch_margin_mode(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("switch_margin_mode", path),
            payload=body,
            use_json=use_json,
        )

    def switch_separate_position_mode(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        body = build_position_payload(payload)
        return self._private_write(
            "POST",
            self._resolve_endpoint("switch_separate_position_mode", path),
            payload=body,
            use_json=use_json,
        )

    def public_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return self._request(method, path, params=params, json_body=json_body, headers=headers)

    def get_funding_balances(self, *, path: str | None = None) -> Any:
        return self._signed_request("GET", self._resolve_endpoint("funding_balances", path))

    def get_user_id(self, *, path: str | None = None) -> Any:
        return self._signed_request("GET", self._resolve_endpoint("user_id", path))

    def get_transfer_history(
        self,
        *,
        start_time: int,
        end_time: int,
        coin: str | None = None,
        page_num: int | None = None,
        page_size: int | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_transfer_history_params(
            start_time=start_time,
            end_time=end_time,
            coin=coin,
            page_num=page_num,
            page_size=page_size,
            params=params,
        )
        return self._signed_request(
            "GET",
            self._resolve_endpoint("transfer_history", path),
            params=request_params,
        )

    def transfer_between_accounts(
        self,
        *,
        amount: str,
        coin: str,
        from_wallet: str,
        to_wallet: str,
        path: str | None = None,
        extra_payload: Mapping[str, Any] | None = None,
    ) -> Any:
        payload = build_transfer_payload(
            amount=amount,
            coin=coin,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            extra_payload=extra_payload,
        )
        return self._signed_request(
            "POST",
            self._resolve_endpoint("funding_transfer", path),
            json_body=payload,
        )

    def get_fiat_rate(
        self,
        symbol_list: str | Sequence[str] | None = None,
        *,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = build_fiat_rate_params(symbol_list=symbol_list, params=params)
        return self._request("GET", self._resolve_endpoint("fiat_rate", path), params=request_params)

    def private_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return self._signed_request(
            method,
            path,
            params=params,
            json_body=json_body,
            headers=headers,
        )

    def _private_write(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any],
        use_json: bool,
    ) -> Any:
        if use_json:
            return self._signed_request(method, path, json_body=payload)
        return self._signed_request(method, path, params=payload)

    def _signed_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        if self.auto_sync_time:
            self.sync_time()

        prepared = self._prepare_signed_components(params=params, json_body=json_body, headers=headers)
        try:
            return self._request(
                method,
                path,
                params=prepared.params,
                json_body=prepared.json_body,
                body_text=prepared.body_text,
                headers=prepared.headers,
            )
        except APIError as exc:
            if not self._response_handler.is_timestamp_error(exc):
                raise

            self.sync_time(force=True)
            prepared = self._prepare_signed_components(params=params, json_body=json_body, headers=headers)
            return self._request(
                method,
                path,
                params=prepared.params,
                json_body=prepared.json_body,
                body_text=prepared.body_text,
                headers=prepared.headers,
            )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        body_text: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        if not self.base_url:
            raise ConfigurationError("base_url is required before sending requests.")
        if not path:
            raise ConfigurationError("Request path is required.")

        request_headers = self._build_headers(headers)
        url = self._build_url(path)
        request_params = clean_mapping(params)
        request_json = clean_mapping(json_body)
        request_body_text = body_text
        if request_body_text is None and request_json:
            request_body_text = serialize_json_body(request_json)

        response = self._transport.request(
            method=method,
            url=url,
            params=request_params or None,
            data=request_body_text,
            headers=request_headers,
            timeout=self.timeout,
        )

        payload = self._response_handler.handle(response)
        return self._maybe_wrap_response(payload)

    def _prepare_signed_components(
        self,
        *,
        params: Mapping[str, Any] | None,
        json_body: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
    ):
        self._signer.api_key = self.api_key
        self._signer.api_secret = self.api_secret
        return self._signer.prepare(params=params, json_body=json_body, headers=headers)

    def _maybe_wrap_response(self, payload: Any) -> Any:
        if not self.response_typed or not isinstance(payload, Mapping):
            return payload
        return SDKResponse.from_payload(
            payload,
            code_fields=self.response_config.code_fields,
            message_fields=self.response_config.message_fields,
        )

    def _resolve_endpoint(self, name: str, explicit_path: str | None) -> str:
        if explicit_path:
            return explicit_path

        configured = self.endpoint_map.get(name, "")
        if configured:
            return configured

        raise ConfigurationError(
            f"Endpoint '{name}' is not configured. Pass path=... or provide endpoint_map in __init__."
        )

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def _build_headers(self, custom_headers: Mapping[str, str] | None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": self.auth_config.content_type,
            "User-Agent": self.user_agent,
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    # Backward-compatible aliases for tests and internal callers
    @property
    def _time_offset_ms(self) -> int:
        return self._time_sync.server_time_offset_ms

    @_time_offset_ms.setter
    def _time_offset_ms(self, value: int) -> None:
        self._time_sync._offset_ms = value

    @property
    def _last_time_sync_monotonic(self) -> float | None:
        return self._time_sync._last_sync_monotonic

    @_last_time_sync_monotonic.setter
    def _last_time_sync_monotonic(self, value: float | None) -> None:
        self._time_sync._last_sync_monotonic = value
