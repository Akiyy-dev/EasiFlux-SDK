from __future__ import annotations

import base64
import hashlib
import hmac
import json as json_lib
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlencode, urljoin

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AuthConfig, DEFAULT_ENDPOINTS, ResponseConfig
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    HTTPStatusError,
    RateLimitError,
    RequestError,
    ResponseParseError,
)


class EasiCoinSDK:
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
        user_agent: str = "EasiCoinSDK/0.1.0",
        auto_sync_time: bool = True,
        time_sync_interval: float = 30.0,
        session: Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.user_agent = user_agent
        self.auto_sync_time = auto_sync_time
        self.time_sync_interval = time_sync_interval

        self.auth_config = auth_config or AuthConfig()
        self.response_config = response_config or ResponseConfig()
        self.endpoint_map: dict[str, str] = dict(DEFAULT_ENDPOINTS)
        if endpoint_map:
            self.endpoint_map.update(endpoint_map)

        self.session = session or self._build_session()
        self._time_offset_ms = 0
        self._last_time_sync_monotonic: float | None = None

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "EasiCoinSDK":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def set_endpoint(self, name: str, path: str) -> None:
        self.endpoint_map[name] = path

    def get_server_time(self, *, path: str | None = None) -> Any:
        return self._request("GET", self._resolve_endpoint("server_time", path))

    def sync_time(self, *, force: bool = False) -> int:
        if not self.auto_sync_time:
            return self._time_offset_ms

        if not force and self._last_time_sync_monotonic is not None:
            elapsed = time.monotonic() - self._last_time_sync_monotonic
            if elapsed < self.time_sync_interval:
                return self._time_offset_ms

        server_time_response = self.get_server_time()
        server_time_ms = self._extract_server_time_ms(server_time_response)
        if server_time_ms is None:
            raise ResponseParseError("Unable to extract server time from EasiCoin response.")

        local_time_ms = int(time.time() * 1000)
        self._time_offset_ms = server_time_ms - local_time_ms
        self._last_time_sync_monotonic = time.monotonic()
        return self._time_offset_ms

    def get_ticker(
        self,
        symbol: str | None = None,
        *,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = dict(params or {})
        if symbol is not None:
            request_params["symbol"] = symbol
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
        request_params = dict(params or {})
        request_params["symbol"] = symbol
        if depth is not None:
            request_params["depth"] = depth
        if limit is not None:
            request_params["depth"] = limit
        return self._request("GET", self._resolve_endpoint("depth", path), params=request_params)

    def get_trading_fee_rate(
        self,
        *,
        symbol: str | None = None,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = dict(params or {})
        if symbol is not None:
            request_params["symbol"] = symbol
        if coin is not None:
            request_params["coin"] = coin
        return self._signed_request("GET", self._resolve_endpoint("fee_rate", path), params=request_params)

    def create_order(
        self,
        order: Mapping[str, Any],
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        return self._private_write(
            "POST",
            self._resolve_endpoint("create_order", path),
            payload=order,
            use_json=use_json,
        )

    def cancel_order(
        self,
        order_query: Mapping[str, Any],
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        return self._private_write(
            "POST",
            self._resolve_endpoint("cancel_order", path),
            payload=order_query,
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
        return self._signed_request(
            "GET",
            self._resolve_endpoint("orders", path),
            params=request_params,
        )

    def get_balances(
        self,
        *,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        request_params = dict(params or {})
        if coin is not None:
            request_params["coin"] = coin
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
        request_params = dict(params or {})
        if symbol is not None:
            request_params["symbol"] = symbol
        if coin is not None:
            request_params["coin"] = coin
        return self._signed_request(
            "GET",
            self._resolve_endpoint("positions", path),
            params=request_params,
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
        payload = {
            "amount": amount,
            "coin": coin,
            "from_wallet": from_wallet,
            "to_wallet": to_wallet,
        }
        if extra_payload:
            payload.update(extra_payload)
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
        request_params = dict(params or {})
        if symbol_list is not None:
            if isinstance(symbol_list, Sequence) and not isinstance(symbol_list, (str, bytes, bytearray)):
                request_params["symbol_list"] = ",".join(str(item) for item in symbol_list)
            else:
                request_params["symbol_list"] = symbol_list
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

        prepared = self._prepare_signed_components(method, path, params=params, json_body=json_body, headers=headers)
        try:
            return self._request(
                method,
                path,
                params=prepared["params"],
                json_body=prepared["json_body"],
                body_text=prepared["body_text"],
                headers=prepared["headers"],
            )
        except APIError as exc:
            if not self._is_timestamp_error(exc):
                raise

            self.sync_time(force=True)
            prepared = self._prepare_signed_components(method, path, params=params, json_body=json_body, headers=headers)
            return self._request(
                method,
                path,
                params=prepared["params"],
                json_body=prepared["json_body"],
                body_text=prepared["body_text"],
                headers=prepared["headers"],
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
        request_params = self._clean_mapping(params)
        request_json = self._clean_mapping(json_body)
        request_body_text = body_text
        if request_body_text is None and request_json:
            request_body_text = self._serialize_json_body(request_json)

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=request_params or None,
                data=request_body_text,
                headers=request_headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RequestError(f"HTTP request failed: {exc}") from exc

        return self._handle_response(response)

    def _prepare_signed_components(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
    ) -> dict[str, Any]:
        self._ensure_credentials()

        prepared_headers = dict(headers or {})
        prepared_params = self._clean_mapping(params)
        prepared_json = self._clean_mapping(json_body)

        timestamp_text = str(self._current_timestamp())
        query_string = self._encode_mapping(prepared_params)
        body_text = self._serialize_json_body(prepared_json) if prepared_json else ""
        recv_window_text = str(self.recv_window) if self.recv_window is not None else ""
        payload = self._build_signature_payload(query_string=query_string, body_text=body_text)
        payload = f"{timestamp_text}{self.api_key}{recv_window_text}{payload}"
        signature = self._sign(payload)

        prepared_headers[self.auth_config.api_key_header] = self.api_key
        prepared_headers[self.auth_config.signature_header] = signature
        prepared_headers[self.auth_config.timestamp_header] = timestamp_text
        if self.recv_window is not None:
            prepared_headers[self.auth_config.recv_window_header] = recv_window_text

        return {
            "headers": prepared_headers,
            "params": prepared_params,
            "json_body": prepared_json,
            "body_text": body_text or None,
        }

    def _build_signature_payload(
        self,
        *,
        query_string: str,
        body_text: str,
    ) -> str:
        if body_text:
            return body_text
        return query_string

    def _sign(self, payload: str) -> str:
        digest = hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        if self.auth_config.signature_encoding == "base64":
            return base64.b64encode(digest).decode("utf-8")
        return digest.hex()

    def _handle_response(self, response: Response) -> Any:
        payload = self._parse_response(response)

        if response.status_code >= 400:
            self._raise_http_error(response, payload)

        if isinstance(payload, Mapping) and not self._is_success_payload(payload):
            self._raise_api_error(payload)

        return payload

    def _parse_response(self, response: Response) -> Any:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or "text/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise ResponseParseError("Response body is not valid JSON.") from exc

        body = response.text.strip()
        if not body:
            return None

        try:
            return response.json()
        except ValueError:
            return body

    def _is_success_payload(self, payload: Mapping[str, Any]) -> bool:
        success_field = self.response_config.success_field
        if success_field and success_field in payload:
            return payload.get(success_field) in self.response_config.success_values

        for field in self.response_config.code_fields:
            if field in payload:
                return payload.get(field) in self.response_config.success_codes

        return True

    def _raise_http_error(self, response: Response, payload: Any) -> None:
        code = self._extract_code(payload)
        message = self._extract_message(payload) or response.reason or "HTTP request failed."

        if response.status_code in {401, 403}:
            raise AuthenticationError(message, code=code, payload=payload)
        if response.status_code == 429:
            raise RateLimitError(message, code=code, payload=payload)

        raise HTTPStatusError(
            message,
            status_code=response.status_code,
            code=code,
            payload=payload,
        )

    def _raise_api_error(self, payload: Mapping[str, Any]) -> None:
        code = self._extract_code(payload)
        message = self._extract_message(payload) or "Exchange returned an error response."

        if code in {26200002, 26200003, 20011005, 26200004, 26200005, 26200010}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {26200006, 26200018, 10200616}:
            raise RateLimitError(message, code=code, payload=payload)
        if isinstance(code, str) and code.lower() in {"auth_failed", "invalid_signature"}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {401, 403, "401", "403"}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {429, "429", "too_many_requests"}:
            raise RateLimitError(message, code=code, payload=payload)

        raise APIError(message, code=code, payload=payload)

    def _extract_code(self, payload: Any) -> Any:
        if not isinstance(payload, Mapping):
            return None
        for field in self.response_config.code_fields:
            if field in payload:
                return payload.get(field)
        return None

    def _extract_message(self, payload: Any) -> str | None:
        if not isinstance(payload, Mapping):
            return str(payload) if payload else None
        for field in self.response_config.message_fields:
            value = payload.get(field)
            if value:
                return str(value)
        return None

    def _extract_server_time_ms(self, payload: Any) -> int | None:
        if not isinstance(payload, Mapping):
            return None

        top_level_time = payload.get("time")
        parsed_top_level_time = self._parse_timestamp_value(top_level_time)
        if parsed_top_level_time is not None:
            return parsed_top_level_time

        data = payload.get("data")
        if not isinstance(data, Mapping):
            return None

        return self._parse_timestamp_value(data.get("time"))

    def _parse_timestamp_value(self, value: Any) -> int | None:
        if value is None:
            return None

        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            return None

        if parsed >= 10**12:
            return parsed
        if parsed >= 10**9:
            return parsed * 1000
        return None

    def _is_timestamp_error(self, exc: APIError) -> bool:
        code = getattr(exc, "code", None)
        if code in {26200002, "26200002"}:
            return True
        message = str(exc).lower()
        return "timestamp" in message or "recv_window" in message

    def _ensure_credentials(self) -> None:
        if not self.api_key:
            raise ConfigurationError("api_key is required for private requests.")
        if not self.api_secret:
            raise ConfigurationError("api_secret is required for private requests.")

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

    def _current_timestamp(self) -> int:
        now = time.time() + (self._time_offset_ms / 1000)
        if self.auth_config.timestamp_unit == "s":
            return int(now)
        return int(now * 1000)

    def _encode_mapping(self, mapping: Mapping[str, Any]) -> str:
        items = self._flatten_items(mapping)
        if self.auth_config.sort_query_for_signature:
            items.sort(key=lambda item: item[0])
        return urlencode(items, doseq=True)

    def _serialize_json_body(self, mapping: Mapping[str, Any]) -> str:
        return json_lib.dumps(mapping, ensure_ascii=False, separators=(",", ":"))

    def _flatten_items(self, mapping: Mapping[str, Any]) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        for key, value in mapping.items():
            if value is None:
                continue
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                for item in value:
                    items.append((key, self._stringify_value(item)))
                continue
            items.append((key, self._stringify_value(value)))
        return items

    def _stringify_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, Mapping):
            return json_lib.dumps(value, separators=(",", ":"), sort_keys=True)
        return str(value)

    def _clean_mapping(self, mapping: Mapping[str, Any] | None) -> dict[str, Any]:
        if not mapping:
            return {}
        return {key: value for key, value in mapping.items() if value is not None}

    def _build_session(self) -> Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "PUT", "DELETE"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
