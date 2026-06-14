from __future__ import annotations

from typing import Any


class SDKError(Exception):
    """Base exception for all SDK errors."""


class ConfigurationError(SDKError):
    """Raised when SDK configuration is incomplete or invalid."""


class RequestError(SDKError):
    """Raised when the HTTP transport layer fails."""


class ResponseParseError(SDKError):
    """Raised when the response body cannot be parsed as expected."""


class APIError(SDKError):
    """Raised when the exchange returns an application-level error."""

    def __init__(self, message: str, *, code: Any = None, payload: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.payload = payload


class AuthenticationError(APIError):
    """Raised when authentication or signature validation fails."""


class RateLimitError(APIError):
    """Raised when the exchange rejects the request due to rate limiting."""


class HTTPStatusError(APIError):
    """Raised when the HTTP status code indicates failure."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: Any = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message, code=code, payload=payload)
        self.status_code = status_code
