from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconnectPolicy:
    max_retries: int = 10
    backoff_factor: float = 1.5
    max_backoff: float = 60.0
    heartbeat_interval: float = 20.0

    def backoff_delay(self, attempt: int) -> float:
        delay = self.backoff_factor**attempt
        return min(delay, self.max_backoff)
