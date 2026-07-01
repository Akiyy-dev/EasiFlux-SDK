from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..config import AuthConfig
from ..exceptions import ConfigurationError
from .serialization import clean_mapping, encode_mapping, serialize_json_body


@dataclass(frozen=True)
class SignedComponents:
    headers: dict[str, str]
    params: dict[str, Any]
    json_body: dict[str, Any]
    body_text: str | None


class Signer:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        auth_config: AuthConfig,
        recv_window: int | None,
        get_timestamp: Callable[[], int],
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.auth_config = auth_config
        self.recv_window = recv_window
        self._get_timestamp = get_timestamp

    def prepare(
        self,
        *,
        params: Mapping[str, Any] | None,
        json_body: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
    ) -> SignedComponents:
        self.ensure_credentials()

        prepared_headers = dict(headers or {})
        prepared_params = clean_mapping(params)
        prepared_json = clean_mapping(json_body)

        timestamp_text = str(self._get_timestamp())
        query_string = encode_mapping(
            prepared_params,
            sort_query=self.auth_config.sort_query_for_signature,
        )
        body_text = serialize_json_body(prepared_json) if prepared_json else ""
        recv_window_text = str(self.recv_window) if self.recv_window is not None else ""
        signature_payload = body_text if body_text else query_string
        payload = f"{timestamp_text}{self.api_key}{recv_window_text}{signature_payload}"
        signature = self.sign(payload)

        prepared_headers[self.auth_config.api_key_header] = self.api_key
        prepared_headers[self.auth_config.signature_header] = signature
        prepared_headers[self.auth_config.timestamp_header] = timestamp_text
        if self.recv_window is not None:
            prepared_headers[self.auth_config.recv_window_header] = recv_window_text

        return SignedComponents(
            headers=prepared_headers,
            params=prepared_params,
            json_body=prepared_json,
            body_text=body_text or None,
        )

    def sign(self, payload: str) -> str:
        digest = hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        if self.auth_config.signature_encoding == "base64":
            return base64.b64encode(digest).decode("utf-8")
        return digest.hex()

    def sign_ws_auth(self, expires_ms: int) -> str:
        """Sign WebSocket private-channel auth payload (GET/realtime{expires})."""
        self.ensure_credentials()
        return self.sign(f"GET/realtime{expires_ms}")

    def ensure_credentials(self) -> None:
        if not self.api_key:
            raise ConfigurationError("api_key is required for private requests.")
        if not self.api_secret:
            raise ConfigurationError("api_secret is required for private requests.")
