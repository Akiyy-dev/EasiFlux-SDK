import asyncio
import os
from pathlib import Path

from easiflux_sdk import AsyncEasiFluxSDK, AuthConfig, OrderRequest, OrderSide, OrderType, ResponseConfig


def load_env_file(file_name: str = ".env.dev") -> None:
    env_path = Path(__file__).resolve().parents[1] / file_name
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    load_env_file()

    api_key = os.getenv("EASICOIN_API_KEY", "")
    api_secret = os.getenv("EASICOIN_API_SECRET", "")
    base_url = os.getenv("EASICOIN_BASE_URL", "https://api.easicoin.io")
    symbol = os.getenv("EASICOIN_SYMBOL", "BTCUSDT")

    async with AsyncEasiFluxSDK(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        sync_on_init=bool(api_key and api_secret),
        auth_config=AuthConfig(signature_encoding="hex"),
        response_config=ResponseConfig(
            code_fields=("code",),
            success_codes=(0, "0"),
            message_fields=("msg", "message"),
        ),
    ) as client:
        print(await client.get_server_time())
        print(await client.get_ticker(symbol=symbol))

        if api_key and api_secret:
            print(await client.get_balances())
            demo_order = OrderRequest(
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                qty="0.001",
                price="1",
            )
            print("OrderRequest payload:", demo_order.to_api_payload())


if __name__ == "__main__":
    asyncio.run(main())
