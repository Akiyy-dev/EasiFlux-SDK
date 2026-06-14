from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SDKResponse(Generic[T]):
    code: int | str
    message: str | None
    data: T | None
    raw: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        data: T | None = None,
        code_fields: tuple[str, ...] = ("code", "errorCode", "status"),
        message_fields: tuple[str, ...] = ("msg", "message", "error", "detail", "errorMessage"),
    ) -> SDKResponse[T]:
        code: int | str = 0
        for field in code_fields:
            if field in payload:
                value = payload[field]
                if isinstance(value, (int, str)):
                    code = value
                    break

        message: str | None = None
        for field in message_fields:
            value = payload.get(field)
            if value:
                message = str(value)
                break

        if data is None and "data" in payload:
            data = payload["data"]  # type: ignore[assignment]

        return cls(code=code, message=message, data=data, raw=payload)
