"""Lightweight observability helpers backed by Logfire."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

try:
    import logfire  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    logfire = None  # type: ignore

SENSITIVE_FIELDS = {
    "content",
    "openai_api_key",
    "password",
    "authorization",
    "api_key",
}
MAX_FIELD_LENGTH = 200
REDACTED_VALUE = "***REDACTED***"


def _to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _truncate_value(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) <= MAX_FIELD_LENGTH:
            return value
        return value[:MAX_FIELD_LENGTH] + "…"
    if isinstance(value, list):
        return [_truncate_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _truncate_value(val) for key, val in value.items()}
    return value


def _sanitize(name: str, value: Any) -> Any:
    if name.lower() in SENSITIVE_FIELDS:
        return REDACTED_VALUE
    return _truncate_value(value)


def get_logger(name: str = "carax") -> logging.Logger:
    """Return the stdlib logger used across the project."""
    return logging.getLogger(name)


class BaseObservability:
    """Minimal observability façade used across the app."""

    enabled: bool = False

    def sanitize_field(self, name: str, value: Any) -> Any:
        return _sanitize(name, value)

    @contextmanager
    def span(self, name: str, **fields: Any) -> Iterator[None]:
        yield

    def log_event(self, **fields: Any) -> None:
        return None


class NoOpObservability(BaseObservability):
    """No-op implementation used when Logfire is disabled."""

    def __init__(self) -> None:
        self.logger = get_logger()
        self.enabled = False


class LogfireObservability(BaseObservability):
    """Logfire-backed observability adapter."""

    def __init__(self, logger: logging.Logger, logfire_module: Any) -> None:
        self.logger = logger
        self.enabled = True
        self._logfire = logfire_module

    def _process_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        return {key: self.sanitize_field(key, value) for key, value in fields.items()}

    @contextmanager
    def span(self, name: str, **fields: Any) -> Iterator[None]:
        processed = self._process_fields(fields)
        start = time.perf_counter()
        span_cm = None
        if self._logfire and hasattr(self._logfire, "span"):
            span_cm = self._logfire.span(name, **processed)
        if span_cm is not None:
            with span_cm:
                try:
                    yield
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.log_event(event="span.end", span=name, duration_ms=duration_ms, **processed)
        else:
            self.logger.debug("span.start %s %s", name, processed)
            try:
                yield
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                self.logger.debug(
                    "span.end %s duration_ms=%s fields=%s", name, f"{duration_ms:.2f}", processed
                )

    def log_event(self, **fields: Any) -> None:
        processed = self._process_fields(fields)
        if self._logfire and hasattr(self._logfire, "event"):
            self._logfire.event(**processed)
        else:
            self.logger.info("event %s", processed)


def init_logfire() -> BaseObservability:
    """Initialise Logfire if enabled, otherwise return a no-op adapter."""

    enabled = _to_bool(os.getenv("LOGFIRE_ENABLED"))
    api_key = os.getenv("LOGFIRE_API_KEY")

    if not enabled or not api_key or logfire is None:
        return NoOpObservability()

    try:  # pragma: no cover - configuration is best-effort
        logfire.configure(api_key=api_key, redact_fields=list(SENSITIVE_FIELDS))
    except Exception:  # pragma: no cover - fallback to no-op on configuration errors
        return NoOpObservability()

    logger = getattr(logfire, "get_logger", None)
    if callable(logger):
        logger_instance = logger("carax")
    else:
        logger_instance = get_logger()

    return LogfireObservability(logger_instance, logfire)


__all__ = [
    "BaseObservability",
    "LogfireObservability",
    "NoOpObservability",
    "get_logger",
    "init_logfire",
]
