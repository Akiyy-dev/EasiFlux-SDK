# AGENTS.md

## Cursor Cloud specific instructions

EasiFlux-SDK is a pure Python library (no server/GUI) for the EasiCoin exchange REST API. Source lives in `src/easiflux_sdk`, tests in `tests/`, and runnable demos in `examples/basic_usage.py` (sync) and `examples/async_usage.py` (async).

The startup update script provisions a virtualenv at `.venv/` with the package installed editable plus dev tools. Always use that interpreter:

- Lint: `.venv/bin/ruff check .`
- Test: `.venv/bin/pytest -q`
- Run sync demo: `.venv/bin/python examples/basic_usage.py`
- Run async demo: `.venv/bin/python examples/async_usage.py`
- Build (CI packaging smoke test): `.venv/bin/python -m build` (requires `.venv/bin/pip install build`)

Notes / gotchas:

- `examples/basic_usage.py` and `examples/async_usage.py` make live HTTPS calls to `https://api.easicoin.io`. Public endpoints (`get_server_time`, `get_ticker`) work without credentials and are the quickest smoke test. Private endpoints require `EASICOIN_API_KEY` / `EASICOIN_API_SECRET`; without them the script prints a reminder and only exercises public endpoints.
- To exercise private endpoints, create a `.env.dev` file at the repo root (gitignored) with `EASICOIN_API_KEY`, `EASICOIN_API_SECRET`, etc. The examples auto-load it.
- The unit tests use stubbed HTTP sessions (sync) and respx (async), so `pytest` requires no network and no credentials.
- The pip distribution name is `EasiFlux-SDK` and the importable package is `easiflux_sdk`. The legacy import `easicoin_sdk` remains as a deprecated shim.
- WebSocket requires optional dependency: `pip install -e ".[websocket]"` or `.[dev]`.
