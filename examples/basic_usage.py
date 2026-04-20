import os
from pathlib import Path

from easicoin_sdk import AuthConfig, EasiCoinSDK, ResponseConfig


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


def main() -> None:
    load_env_file()

    api_key = os.getenv("EASICOIN_API_KEY", "")
    api_secret = os.getenv("EASICOIN_API_SECRET", "")
    base_url = os.getenv("EASICOIN_BASE_URL", "https://api.easicoin.io")
    symbol = os.getenv("EASICOIN_SYMBOL", "BTCUSDT")
    recv_window = int(os.getenv("EASICOIN_RECV_WINDOW", "5000"))

    sdk = EasiCoinSDK(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        recv_window=recv_window,
        auth_config=AuthConfig(
            signature_encoding="hex",
        ),
        response_config=ResponseConfig(
            code_fields=("code",),
            success_codes=(0, "0"),
            message_fields=("msg", "message"),
        ),
    )

    if not sdk.api_key or not sdk.api_secret:
        print("Please fill EASICOIN_API_KEY and EASICOIN_API_SECRET in .env.dev before calling private endpoints.")
        print(sdk.get_server_time())
        print(sdk.get_ticker(symbol=symbol))
        return

    print(sdk.get_server_time())
    print(sdk.get_ticker(symbol=symbol))
    print(sdk.get_kline(symbol=symbol, interval="1", limit=5))
    print(sdk.get_depth(symbol=symbol, depth=20))
    print(sdk.get_balances())
    print(sdk.get_positions(symbol=symbol))


if __name__ == "__main__":
    main()