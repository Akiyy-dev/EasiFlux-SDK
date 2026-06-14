"""Deprecated compatibility shim for the renamed ``easiflux_sdk`` package."""

from __future__ import annotations

import warnings

from easiflux_sdk import (
    APIError,
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
)

_DEPRECATION_MESSAGE = (
    "The easicoin_sdk package is deprecated; use easiflux_sdk instead. "
    "EasiCoinSDK is an alias for EasiFluxSDK and will be removed in v1.0."
)

warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)

EasiCoinSDK = EasiFluxSDK

__all__ = [
    "APIError",
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
]
