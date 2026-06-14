from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections.abc import Awaitable, Callable

from ..config import TimestampUnit
from ..exceptions import ResponseParseError
from .response_handler import ResponseHandler

FetchServerTime = Callable[[], object | Awaitable[object]]


class TimeSyncManager:
    def __init__(
        self,
        response_handler: ResponseHandler,
        *,
        enabled: bool = True,
        interval: float = 30.0,
        sync_on_init: bool = False,
        timestamp_unit: TimestampUnit = "ms",
    ) -> None:
        self.response_handler = response_handler
        self.enabled = enabled
        self.interval = interval
        self.sync_on_init = sync_on_init
        self.timestamp_unit = timestamp_unit

        self._offset_ms = 0
        self._last_sync_monotonic: float | None = None
        self._lock = threading.Lock()
        self._async_lock: asyncio.Lock | None = None

    def _get_async_lock(self) -> asyncio.Lock:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    @property
    def server_time_offset_ms(self) -> int:
        return self._offset_ms

    def get_timestamp(self) -> int:
        now = time.time() + (self._offset_ms / 1000)
        if self.timestamp_unit == "s":
            return int(now)
        return int(now * 1000)

    def should_sync(self, *, force: bool = False) -> bool:
        if not self.enabled:
            return False
        if force:
            return True
        if self._last_sync_monotonic is None:
            return True
        elapsed = time.monotonic() - self._last_sync_monotonic
        return elapsed >= self.interval

    def update_offset(self, server_time_ms: int) -> int:
        with self._lock:
            local_time_ms = int(time.time() * 1000)
            self._offset_ms = server_time_ms - local_time_ms
            self._last_sync_monotonic = time.monotonic()
            return self._offset_ms

    def sync(
        self,
        fetch_server_time: FetchServerTime,
        *,
        force: bool = False,
    ) -> int:
        if not self.enabled:
            return self._offset_ms
        if not self.should_sync(force=force):
            return self._offset_ms

        server_time_response = fetch_server_time()
        server_time_ms = self.response_handler.extract_server_time_ms(server_time_response)
        if server_time_ms is None:
            raise ResponseParseError("Unable to extract server time from EasiCoin response.")

        return self.update_offset(server_time_ms)

    async def async_sync(
        self,
        fetch_server_time: FetchServerTime,
        *,
        force: bool = False,
    ) -> int:
        if not self.enabled:
            return self._offset_ms
        if not self.should_sync(force=force):
            return self._offset_ms

        async with self._get_async_lock():
            if not self.should_sync(force=force):
                return self._offset_ms

            server_time_response = fetch_server_time()
            if inspect.isawaitable(server_time_response):
                server_time_response = await server_time_response

            server_time_ms = self.response_handler.extract_server_time_ms(server_time_response)
            if server_time_ms is None:
                raise ResponseParseError("Unable to extract server time from EasiCoin response.")

            return self.update_offset(server_time_ms)

