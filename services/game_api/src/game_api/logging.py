"""Structured JSON logging for Game API."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

_logger = logging.getLogger("game_api")


def log_event(
    *,
    level: str = "INFO",
    service: str = "game-api",
    request_id: str = "",
    session_id: str = "",
    route: str = "",
    method: str = "",
    status_code: int = 0,
    duration_ms: float = 0.0,
    action_type: str = "",
    target_id: str = "",
    state_version: int = 0,
    error_code: str = "",
    message: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured JSON log record."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "service": service,
        "request_id": request_id,
        "session_id": session_id,
        "route": route,
        "method": method,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "action_type": action_type,
        "target_id": target_id,
        "state_version": state_version,
        "error_code": error_code,
        "message": message,
    }
    if extra:
        record.update(extra)

    log_fn = {
        "DEBUG": _logger.debug,
        "INFO": _logger.info,
        "WARNING": _logger.warning,
        "ERROR": _logger.error,
        "CRITICAL": _logger.critical,
    }.get(level.upper(), _logger.info)

    log_fn(json.dumps(record, ensure_ascii=False))


class RequestTimer:
    """Context-style timer for request duration tracking."""

    def __init__(self) -> None:
        self._start: float = 0.0

    def start(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0
