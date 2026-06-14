from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.logging import get_logger
from ..core.retry import RetryPolicy
from ..exceptions import RequestError

logger = get_logger(__name__)


class RequestsTransport:
    def __init__(
        self,
        session: Session | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._session = session or self._build_session(retry_policy or RetryPolicy())
        self._owns_session = session is None

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float,
    ) -> requests.Response:
        logger.debug("HTTP %s %s params=%s", method.upper(), url, params)
        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                params=params or None,
                data=data,
                headers=dict(headers or {}),
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise RequestError(f"HTTP request failed: {exc}") from exc

        logger.debug("HTTP %s %s -> %s", method.upper(), url, response.status_code)
        return response

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    @staticmethod
    def _build_session(retry_policy: RetryPolicy) -> Session:
        session = Session()
        retry = Retry(**retry_policy.as_urllib3_kwargs())
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
