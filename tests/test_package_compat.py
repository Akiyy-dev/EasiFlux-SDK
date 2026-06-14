from __future__ import annotations

import warnings

from easiflux_sdk import EasiFluxSDK


def test_easiflux_sdk_public_exports() -> None:
    import easiflux_sdk

    assert easiflux_sdk.EasiFluxSDK is EasiFluxSDK
    assert "EasiFluxSDK" in easiflux_sdk.__all__


def test_easicoin_sdk_shim_reexports_client() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import easicoin_sdk  # noqa: F401

    assert any(issubclass(item.category, DeprecationWarning) for item in caught)
    assert easicoin_sdk.EasiCoinSDK is EasiFluxSDK
    assert easicoin_sdk.EasiFluxSDK is EasiFluxSDK


def test_easicoin_sdk_shim_exports_match_easiflux_sdk() -> None:
    import easiflux_sdk

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("ignore")
        import easicoin_sdk

    shared = {
        "APIError",
        "AuthConfig",
        "AuthenticationError",
        "ConfigurationError",
        "HTTPStatusError",
        "RateLimitError",
        "RequestError",
        "ResponseConfig",
        "ResponseParseError",
        "SDKError",
    }
    for name in shared:
        assert getattr(easicoin_sdk, name) is getattr(easiflux_sdk, name)
