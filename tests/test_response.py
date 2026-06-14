from __future__ import annotations

from easiflux_sdk.config import ResponseConfig
from easiflux_sdk.core.response_handler import ResponseHandler
from easiflux_sdk.response import SDKResponse


def test_sdk_response_from_payload() -> None:
    payload = {"code": 0, "message": "success", "data": {"order_id": "1"}}
    response = SDKResponse.from_payload(payload)

    assert response.code == 0
    assert response.message == "success"
    assert response.data == {"order_id": "1"}
    assert response.raw == payload


def test_response_handler_detects_timestamp_error() -> None:
    from easiflux_sdk.exceptions import APIError

    handler = ResponseHandler(ResponseConfig())
    exc = APIError("timestamp expired", code=26200002)

    assert handler.is_timestamp_error(exc) is True
