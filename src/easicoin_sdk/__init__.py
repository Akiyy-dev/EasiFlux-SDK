"""Deprecated compatibility shim for the renamed ``easiflux_sdk`` package."""

from __future__ import annotations

import warnings

from easiflux_sdk import (
    APIError,
    AsyncEasiFluxSDK,
    AuthConfig,
    AuthenticationError,
    ConfigurationError,
    EasiFluxSDK,
    HTTPStatusError,
    RateLimitError,
    RequestError,
    ResponseConfig,
    ResponseParseError,
    SDKError,
    SDKResponse,
)

_DEPRECATION_MESSAGE = (
    "The easicoin_sdk package is deprecated; use easiflux_sdk instead. "
    "EasiCoinSDK is an alias for EasiFluxSDK and will be removed in v1.0."
)

warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)

EasiCoinSDK = EasiFluxSDK
AsyncEasiCoinSDK = AsyncEasiFluxSDK

__all__ = [
    "APIError",
    "AsyncEasiCoinSDK",
    "AsyncEasiFluxSDK",
    "AuthConfig",
    "AuthenticationError",
    "ConfigurationError",
    "EasiCoinSDK",
    "EasiFluxSDK",
    "HTTPStatusError",
    "RateLimitError",
    "RequestError",
    "ResponseConfig",
    "ResponseParseError",
    "SDKError",
    "SDKResponse",
]
