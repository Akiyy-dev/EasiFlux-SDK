from __future__ import annotations

from easiflux_sdk.config import AuthConfig
from easiflux_sdk.core.auth import Signer


def test_signer_builds_hex_signature() -> None:
    signer = Signer(
        api_key="key",
        api_secret="secret",
        auth_config=AuthConfig(signature_encoding="hex"),
        recv_window=5000,
        get_timestamp=lambda: 1700000000000,
    )
    components = signer.prepare(
        params={"symbol": "BTCUSDT"},
        json_body=None,
        headers=None,
    )

    assert components.headers["Access-Key"] == "key"
    assert components.headers["Access-Timestamp"] == "1700000000000"
    assert len(components.headers["Access-Sign"]) == 64


def test_signer_serializes_post_body_for_signature() -> None:
    signer = Signer(
        api_key="key",
        api_secret="secret",
        auth_config=AuthConfig(),
        recv_window=5000,
        get_timestamp=lambda: 1,
    )
    components = signer.prepare(
        params=None,
        json_body={"symbol": "BTCUSDT", "side": "Buy"},
        headers=None,
    )

    assert components.body_text == '{"symbol":"BTCUSDT","side":"Buy"}'


def test_signer_builds_ws_auth_signature() -> None:
    signer = Signer(
        api_key="key",
        api_secret="secret",
        auth_config=AuthConfig(signature_encoding="hex"),
        recv_window=5000,
        get_timestamp=lambda: 1700000000000,
    )

    signature = signer.sign_ws_auth(1662350400000)

    assert len(signature) == 64
