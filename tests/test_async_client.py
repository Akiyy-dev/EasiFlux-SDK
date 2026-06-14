from __future__ import annotations

import httpx
import pytest
import respx

from easiflux_sdk import AsyncEasiFluxSDK, OrderRequest, OrderSide, OrderType


@pytest.mark.asyncio
@respx.mock
async def test_async_get_ticker() -> None:
    route = respx.get("https://api.easicoin.io/futures/public/v1/market/tickers").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {}})
    )

    async with AsyncEasiFluxSDK(sync_on_init=False) as client:
        response = await client.get_ticker(symbol="BTCUSDT")

    assert route.called
    assert response["code"] == 0


@pytest.mark.asyncio
@respx.mock
async def test_async_create_order_with_model() -> None:
    route = respx.post("https://api.easicoin.io/futures/private/v1/create-order").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {"order_id": "1"}})
    )

    async with AsyncEasiFluxSDK(
        api_key="key",
        api_secret="secret",
        auto_sync_time=False,
        sync_on_init=False,
    ) as client:
        request = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            qty="0.001",
            price="50000",
        )
        response = await client.create_order(request)

    assert route.called
    assert response["code"] == 0
