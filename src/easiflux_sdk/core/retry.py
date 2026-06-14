from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    total: int = 3
    connect: int = 3
    read: int = 3
    backoff_factor: float = 0.3
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504)

    def as_urllib3_kwargs(self) -> dict[str, object]:
        return {
            "total": self.total,
            "connect": self.connect,
            "read": self.read,
            "backoff_factor": self.backoff_factor,
            "status_forcelist": self.status_forcelist,
            "allowed_methods": frozenset({"GET", "POST", "PUT", "DELETE"}),
        }
