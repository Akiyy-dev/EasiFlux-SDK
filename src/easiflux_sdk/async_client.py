from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import DEFAULT_ENDPOINTS, AuthConfig, ResponseConfig
from .core.auth import Signer
from .core.events import EventEmitter
from .core.operations import (
    build_create_order_payload,
    build_order_query_params,
    build_ticker_params,
)
from .core.response_handler import ResponseHandler
from .core.serialization import clean_mapping, serialize_json_body
from .core.time_sync import TimeSyncManager
from .exceptions import APIError, ConfigurationError
from .response import SDKResponse
from .transport.async_ import HttpxAsyncTransport
from .websocket.manager import WebSocketManager


class AsyncEasiFluxSDK:
    """Asynchronous SDK for the official EasiCoin REST API."""

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
        user_agent: str = "EasiFluxSDK/0.2.0",
        auto_sync_time: bool = True,
        time_sync_interval: float = 30.0,
        sync_on_init: bool = False,
        response_typed: bool = False,
        ws_url: str | None = None,
        client: httpx.AsyncClient | None = None,
        transport: HttpxAsyncTransport | None = None,
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
        self._transport = transport or HttpxAsyncTransport(client=client)
        self.events = EventEmitter()
        self.ws = WebSocketManager(
            ws_url=ws_url or self._default_ws_url(),
            api_key=api_key,
            api_secret=api_secret,
            auth_config=self.auth_config,
            signer=self._signer,
            time_sync=self._time_sync,
            events=self.events,
        )
        self._init_synced = False

    def _default_ws_url(self) -> str:
        if self.base_url.startswith("https://"):
            return self.base_url.replace("https://", "wss://", 1) + "/ws"
        if self.base_url.startswith("http://"):
            return self.base_url.replace("http://", "ws://", 1) + "/ws"
        return f"wss://{self.base_url}/ws"

    async def _ensure_init_sync(self) -> None:
        if self._init_synced or not (self.auto_sync_time and self.sync_on_init):
            return
        await self.sync_time(force=True)
        self._init_synced = True

    @property
    def server_time_offset_ms(self) -> int:
        return self._time_sync.server_time_offset_ms

    async def close(self) -> None:
        await self.ws.close()
        await self._transport.close()

    async def __aenter__(self) -> AsyncEasiFluxSDK:
        await self._ensure_init_sync()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    def on(self, event: str, handler: Callable[[Any], Any | Awaitable[Any]] | None = None):
        return self.events.on(event, handler)

    def set_endpoint(self, name: str, path: str) -> None:
        self.endpoint_map[name] = path

    async def get_server_time(self, *, path: str | None = None) -> Any:
        return await self._request("GET", self._resolve_endpoint("server_time", path))

    async def sync_time(self, *, force: bool = False) -> int:
        return await self._time_sync.async_sync(self.get_server_time, force=force)

    async def get_ticker(
        self,
        symbol: str | None = None,
        *,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        await self._ensure_init_sync()
        request_params = build_ticker_params(symbol=symbol, params=params)
        return await self._request("GET", self._resolve_endpoint("ticker", path), params=request_params)

    async def create_order(
        self,
        order: Mapping[str, Any] | Any,
        *,
        path: str | None = None,
        use_json: bool = True,
    ) -> Any:
        await self._ensure_init_sync()
        payload = build_create_order_payload(order)
        return await self._private_write(
            "POST",
            self._resolve_endpoint("create_order", path),
            payload=payload,
            use_json=use_json,
        )

    async def get_balances(
        self,
        *,
        coin: str | None = None,
        path: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        await self._ensure_init_sync()
        request_params = build_order_query_params(coin=coin, params=params)
        return await self._signed_request(
            "GET",
            self._resolve_endpoint("balances", path),
            params=request_params,
        )

    async def public_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request(method, path, params=params, json_body=json_body, headers=headers)

    async def private_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._signed_request(
            method,
            path,
            params=params,
            json_body=json_body,
            headers=headers,
        )

    async def _private_write(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any],
        use_json: bool,
    ) -> Any:
        if use_json:
            return await self._signed_request(method, path, json_body=payload)
        return await self._signed_request(method, path, params=payload)

    async def _signed_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        if self.auto_sync_time:
            await self.sync_time()

        prepared = self._prepare_signed_components(params=params, json_body=json_body, headers=headers)
        try:
            return await self._request(
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

            await self.sync_time(force=True)
            prepared = self._prepare_signed_components(params=params, json_body=json_body, headers=headers)
            return await self._request(
                method,
                path,
                params=prepared.params,
                json_body=prepared.json_body,
                body_text=prepared.body_text,
                headers=prepared.headers,
            )

    async def _request(
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

        response = await self._transport.request(
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
