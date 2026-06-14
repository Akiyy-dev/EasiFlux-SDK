from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ..core.logging import get_logger
from ..core.retry import RetryPolicy
from ..exceptions import RequestError

logger = get_logger(__name__)


class HttpxAsyncTransport:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        self._owns_client = client is None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        logger.debug("HTTP %s %s params=%s", method.upper(), url, params)
        attempts = max(1, self._retry_policy.total)
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method=method.upper(),
                    url=url,
                    params=params or None,
                    content=data,
                    headers=dict(headers or {}),
                    timeout=timeout,
                )
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt + 1 >= attempts:
                    raise RequestError(f"HTTP request failed: {exc}") from exc
                continue

            if response.status_code in self._retry_policy.status_forcelist and attempt + 1 < attempts:
                continue

            logger.debug("HTTP %s %s -> %s", method.upper(), url, response.status_code)
            return response

        raise RequestError(f"HTTP request failed: {last_exc}")

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
