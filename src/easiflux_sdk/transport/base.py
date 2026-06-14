from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ..core.response_handler import HTTPResponse


class SyncTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float,
    ) -> HTTPResponse: ...

    def close(self) -> None: ...
