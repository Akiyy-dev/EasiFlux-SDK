from __future__ import annotations

import logging

_LOG_NAMESPACE = "easiflux_sdk"
_configured = False


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or _LOG_NAMESPACE)


def configure_logging(
    *,
    level: int | str = logging.WARNING,
    debug: bool = False,
    log_requests: bool = False,
    log_signatures: bool = False,
) -> None:
    global _configured

    if debug:
        level = logging.DEBUG

    logger = get_logger()
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
        logger.addHandler(handler)

    logger.debug(
        "Logging configured: level=%s log_requests=%s log_signatures=%s",
        level,
        log_requests,
        log_signatures,
    )
    _configured = True


def is_logging_configured() -> bool:
    return _configured


def redact_secret(value: str, *, visible: int = 4) -> str:
    if len(value) <= visible:
        return "***"
    return f"{value[:visible]}***"
