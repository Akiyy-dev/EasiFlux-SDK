from __future__ import annotations

from typing import Any, cast

import pytest

from easicoin_sdk import APIError, EasiCoinSDK


class DummyResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.reason = "OK"
        self.headers = {"Content-Type": "application/json"}
        self.text = ""

    def json(self) -> dict[str, Any]:
        return self._payload


def test_public_request_uses_official_default_base_url() -> None:
    captured: dict[str, Any] = {}

    class SessionStub:
        def request(self, **kwargs: Any) -> DummyResponse:
            captured.update(kwargs)
            return DummyResponse({"code": 0, "message": "success", "data": {}})

        def close(self) -> None:
            return None

    sdk = EasiCoinSDK(session=cast(Any, SessionStub()))

    response = sdk.get_ticker(symbol="BTCUSDT")

    assert response["code"] == 0
    assert captured["method"] == "GET"
    assert captured["url"] == "https://api.easicoin.io/futures/public/v1/market/tickers"
    assert captured["params"] == {"symbol": "BTCUSDT"}


def test_private_request_adds_auth_headers_and_json_body() -> None:
    captured: dict[str, Any] = {}

    class SessionStub:
        def request(self, **kwargs: Any) -> DummyResponse:
            captured.update(kwargs)
            return DummyResponse({"code": 0, "message": "success", "data": {"order_id": "1"}})

        def close(self) -> None:
            return None

    sdk = EasiCoinSDK(
        api_key="test-key",
        api_secret="test-secret",
        auto_sync_time=False,
        session=cast(Any, SessionStub()),
    )

    sdk.create_order(
        {
            "symbol": "BTCUSDT",
            "position_idx": 1,
            "side": "Buy",
            "order_type": "Limit",
            "price": "50000",
            "qty": "0.001",
        }
    )

    headers = captured["headers"]
    assert headers["Access-Key"] == "test-key"
    assert "Access-Sign" in headers
    assert "Access-Timestamp" in headers
    assert headers["Recv-Window"] == "5000"
    assert captured["data"] == '{"symbol":"BTCUSDT","position_idx":1,"side":"Buy","order_type":"Limit","price":"50000","qty":"0.001"}'


def test_sync_time_updates_local_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = EasiCoinSDK(auto_sync_time=True)
    target_server_time = 1_700_000_001_500

    monkeypatch.setattr(sdk, "get_server_time", lambda: {"code": 0, "data": {}, "time": target_server_time})
    monkeypatch.setattr("time.time", lambda: 1_700_000_000.0)

    offset = sdk.sync_time(force=True)

    assert offset == 1500
    assert sdk._time_offset_ms == 1500


def test_private_request_retries_once_on_timestamp_error(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = EasiCoinSDK(api_key="test-key", api_secret="test-secret")
    sync_calls: list[bool] = []
    request_calls = 0

    monkeypatch.setattr(sdk, "sync_time", lambda force=False: sync_calls.append(force) or 0)

    def fake_prepare(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "params": {},
            "json_body": {},
            "body_text": None,
            "headers": {},
        }

    def fake_request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal request_calls
        request_calls += 1
        if request_calls == 1:
            raise APIError("timestamp error", code=26200002)
        return {"code": 0, "message": "success", "data": {}}

    monkeypatch.setattr(sdk, "_prepare_signed_components", fake_prepare)
    monkeypatch.setattr(sdk, "_request", fake_request)

    response = sdk.private_request("GET", "/futures/private/v1/account/balance")

    assert response["code"] == 0
    assert request_calls == 2
    assert sync_calls == [False, True]
