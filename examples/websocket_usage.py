import asyncio
import os
from pathlib import Path

from easiflux_sdk import AsyncEasiFluxSDK, configure_logging


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
    configure_logging(debug=True)

    api_key = os.getenv("EASICOIN_API_KEY", "")
    api_secret = os.getenv("EASICOIN_API_SECRET", "")
    symbol = os.getenv("EASICOIN_SYMBOL", "BTCUSDT")

    async with AsyncEasiFluxSDK(
        api_key=api_key,
        api_secret=api_secret,
        sync_on_init=bool(api_key and api_secret),
    ) as client:

        @client.on("ticker")
        async def on_ticker(event: dict) -> None:
            print("ticker event:", event)

        await client.ws.subscribe("ticker", {"symbol": symbol}, callback=on_ticker)
        print("Subscribed to ticker; waiting for events (Ctrl+C to exit)...")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
