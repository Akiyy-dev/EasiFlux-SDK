from __future__ import annotations

import pytest
from conftest import DummyResponse

from easiflux_sdk import EasiFluxSDK
from easiflux_sdk.config import ResponseConfig
from easiflux_sdk.core.response_handler import ResponseHandler
from easiflux_sdk.core.time_sync import TimeSyncManager


def test_time_sync_manager_updates_offset() -> None:
    manager = TimeSyncManager(ResponseHandler(ResponseConfig()))

    offset = manager.update_offset(1_700_000_001_500)

    assert offset == manager.server_time_offset_ms
    assert manager.get_timestamp() > 0


def test_sync_time_on_init_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    class SessionStub:
        def request(self, **kwargs):  # type: ignore[no-untyped-def]
            return DummyResponse({"code": 0, "time": 1_700_000_001_500})

        def close(self) -> None:
            return None

    monkeypatch.setattr("time.time", lambda: 1_700_000_000.0)

    sdk = EasiFluxSDK(session=SessionStub(), sync_on_init=True, auto_sync_time=True)  # type: ignore[arg-type]

    assert sdk.server_time_offset_ms == 1500
