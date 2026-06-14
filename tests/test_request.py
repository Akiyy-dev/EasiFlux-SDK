from __future__ import annotations

from typing import Any, cast

from easiflux_sdk import EasiFluxSDK


class DummyResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.reason = "OK"
        self.headers = {"Content-Type": "application/json"}
        self.text = ""

    def json(self) -> dict[str, Any]:
        return self._payload


def test_request_builds_absolute_url_from_endpoint() -> None:
    captured: dict[str, Any] = {}

    class SessionStub:
        def request(self, **kwargs: Any) -> DummyResponse:
            captured.update(kwargs)
            return DummyResponse({"code": 0})

        def close(self) -> None:
            return None

    sdk = EasiFluxSDK(session=cast(Any, SessionStub()), sync_on_init=False)
    sdk.get_server_time()

    assert captured["url"] == "https://api.easicoin.io/futures/public/v1/market/time"


def test_response_handler_maps_http_401_to_auth_error() -> None:
    from easiflux_sdk.config import ResponseConfig
    from easiflux_sdk.core.response_handler import ResponseHandler
    from easiflux_sdk.exceptions import AuthenticationError

    handler = ResponseHandler(ResponseConfig())

    response = DummyResponse({"code": 401, "message": "auth"}, status_code=401)

    try:
        handler.handle(response)
    except AuthenticationError as exc:
        assert exc.code == 401
    else:
        raise AssertionError("Expected AuthenticationError")
