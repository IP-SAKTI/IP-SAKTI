"""
ip_sakti.utils.logging_config — Structured logging setup.

Call ``configure_logging()`` once at application startup.
All other modules should use the standard ``logging.getLogger(__name__)``
pattern — no direct dependency on this module is needed after startup.
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
import sys
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Emitted fields:
        timestamp, level, logger, message, [exc_info], [extra fields]
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Forward any extra fields attached via `logging.info(..., extra={...})`
        standard_attrs = logging.LogRecord(
            "", 0, "", 0, "", (), None
        ).__dict__.keys()
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(
    level: str | None = None,
    fmt: str | None = None,
) -> None:
    """
    Configure the root logger for the entire application.

    Should be called **once** at application startup (e.g. in the FastAPI
    lifespan or the Streamlit entry point).

    Parameters
    ----------
    level:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        Defaults to the ``LOG_LEVEL`` environment variable, then ``INFO``.
    fmt:
        Log format: ``"json"`` or ``"text"``.
        Defaults to the ``LOG_FORMAT`` environment variable, then ``"json"``.
    """
    effective_level = (
        level
        or os.environ.get("LOG_LEVEL", "INFO")
    ).upper()

    effective_format = (
        fmt
        or os.environ.get("LOG_FORMAT", "json")
    ).lower()

    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)

    # Remove any handlers that may have been added by imported libraries
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(effective_level)

    if effective_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers at WARNING level
    for noisy in (
        "httpx",
        "httpcore",
        "uvicorn.access",
        "sentence_transformers",
        "faiss",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging configured",
        extra={"level": effective_level, "format": effective_format},
    )


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper — returns a named logger.

    Equivalent to ``logging.getLogger(name)``.
    Modules may use this instead of importing ``logging`` directly.
    """
    return logging.getLogger(name)
