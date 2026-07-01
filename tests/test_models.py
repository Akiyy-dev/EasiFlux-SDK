from __future__ import annotations

from easiflux_sdk.models import OrderRequest, OrderSide, OrderType, TimeInForce


def test_order_request_to_api_payload() -> None:
    request = OrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        qty="0.001",
        price="50000",
        position_idx=1,
        time_in_force=TimeInForce.GOOD_TILL_CANCEL,
        order_link_id="demo-001",
    )

    payload = request.to_api_payload()

    assert payload == {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "order_type": "Limit",
        "qty": "0.001",
        "price": "50000",
        "position_idx": 1,
        "time_in_force": "GoodTillCancel",
        "order_link_id": "demo-001",
    }


def test_create_order_accepts_order_request() -> None:
    from typing import Any, cast

    from conftest import DummyResponse

    from easiflux_sdk import EasiFluxSDK

    captured: dict[str, Any] = {}

    class SessionStub:
        def request(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return DummyResponse({"code": 0, "data": {"order_id": "1"}})

        def close(self) -> None:
            return None

    sdk = EasiFluxSDK(
        api_key="key",
        api_secret="secret",
        auto_sync_time=False,
        sync_on_init=False,
        session=cast(Any, SessionStub()),
    )
    request = OrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        qty="0.001",
        price="50000",
        position_idx=1,
    )
    sdk.create_order(request)

    assert '"side":"Buy"' in captured["data"]
