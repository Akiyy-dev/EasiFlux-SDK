from __future__ import annotations

from typing import Any


class DummyResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.reason = "OK"
        self.headers = {"Content-Type": "application/json"}
        self.text = ""

    def json(self) -> dict[str, Any]:
        return self._payload
