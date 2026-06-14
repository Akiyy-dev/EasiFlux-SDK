from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ..config import ResponseConfig
from ..exceptions import (
    APIError,
    AuthenticationError,
    HTTPStatusError,
    RateLimitError,
    ResponseParseError,
)


class HTTPResponse(Protocol):
    status_code: int
    reason: str
    headers: Mapping[str, str]
    text: str

    def json(self) -> Any: ...


class ResponseHandler:
    def __init__(self, response_config: ResponseConfig) -> None:
        self.response_config = response_config

    def parse_response(self, response: HTTPResponse) -> Any:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or "text/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise ResponseParseError("Response body is not valid JSON.") from exc

        body = response.text.strip()
        if not body:
            return None

        try:
            return response.json()
        except ValueError:
            return body

    def handle(self, response: HTTPResponse) -> Any:
        payload = self.parse_response(response)

        if response.status_code >= 400:
            self.raise_http_error(response, payload)

        if isinstance(payload, Mapping) and not self.is_success_payload(payload):
            self.raise_api_error(payload)

        return payload

    def is_success_payload(self, payload: Mapping[str, Any]) -> bool:
        success_field = self.response_config.success_field
        if success_field and success_field in payload:
            return payload.get(success_field) in self.response_config.success_values

        for field in self.response_config.code_fields:
            if field in payload:
                return payload.get(field) in self.response_config.success_codes

        return True

    def raise_http_error(self, response: HTTPResponse, payload: Any) -> None:
        code = self.extract_code(payload)
        message = self.extract_message(payload) or response.reason or "HTTP request failed."

        if response.status_code in {401, 403}:
            raise AuthenticationError(message, code=code, payload=payload)
        if response.status_code == 429:
            raise RateLimitError(message, code=code, payload=payload)

        raise HTTPStatusError(
            message,
            status_code=response.status_code,
            code=code,
            payload=payload,
        )

    def raise_api_error(self, payload: Mapping[str, Any]) -> None:
        code = self.extract_code(payload)
        message = self.extract_message(payload) or "Exchange returned an error response."

        if code in {26200002, 26200003, 20011005, 26200004, 26200005, 26200010}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {26200006, 26200018, 10200616}:
            raise RateLimitError(message, code=code, payload=payload)
        if isinstance(code, str) and code.lower() in {"auth_failed", "invalid_signature"}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {401, 403, "401", "403"}:
            raise AuthenticationError(message, code=code, payload=payload)
        if code in {429, "429", "too_many_requests"}:
            raise RateLimitError(message, code=code, payload=payload)

        raise APIError(message, code=code, payload=payload)

    def extract_code(self, payload: Any) -> Any:
        if not isinstance(payload, Mapping):
            return None
        for field in self.response_config.code_fields:
            if field in payload:
                return payload.get(field)
        return None

    def extract_message(self, payload: Any) -> str | None:
        if not isinstance(payload, Mapping):
            return str(payload) if payload else None
        for field in self.response_config.message_fields:
            value = payload.get(field)
            if value:
                return str(value)
        return None

    def is_timestamp_error(self, exc: APIError) -> bool:
        code = getattr(exc, "code", None)
        if code in {26200002, "26200002"}:
            return True
        message = str(exc).lower()
        return "timestamp" in message or "recv_window" in message

    def extract_server_time_ms(self, payload: Any) -> int | None:
        if not isinstance(payload, Mapping):
            return None

        top_level_time = payload.get("time")
        parsed_top_level_time = self.parse_timestamp_value(top_level_time)
        if parsed_top_level_time is not None:
            return parsed_top_level_time

        data = payload.get("data")
        if not isinstance(data, Mapping):
            return None

        return self.parse_timestamp_value(data.get("time"))

    @staticmethod
    def parse_timestamp_value(value: Any) -> int | None:
        if value is None:
            return None

        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            return None

        if parsed >= 10**12:
            return parsed
        if parsed >= 10**9:
            return parsed * 1000
        return None
