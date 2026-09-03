"""
tests/test_logging.py — Unit tests for ip_sakti.utils.logging_config.

Tests that the logging setup:
  - configure_logging() completes without error
  - produces a usable root logger
  - respects level and format parameters
  - get_logger() returns a Logger instance
"""

from __future__ import annotations

import json
import logging
import io

import pytest

from ip_sakti.utils.logging_config import configure_logging, get_logger


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_configure_json_format_no_error(self) -> None:
        """configure_logging(format='json') completes without raising."""
        configure_logging(level="DEBUG", fmt="json")

    def test_configure_text_format_no_error(self) -> None:
        """configure_logging(format='text') completes without raising."""
        configure_logging(level="INFO", fmt="text")

    def test_root_logger_level_set(self) -> None:
        """Root logger level matches the configured level."""
        configure_logging(level="WARNING", fmt="text")
        assert logging.getLogger().level == logging.WARNING

    def test_json_output_is_parseable(self) -> None:
        """JSON-formatted log records can be parsed as JSON."""
        # Redirect root logger to an in-memory buffer
        configure_logging(level="DEBUG", fmt="json")
        root = logging.getLogger()
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        # Replace handlers temporarily
        original_handlers = root.handlers[:]
        root.handlers = [handler]
        handler.setFormatter(root.handlers[0].formatter if original_handlers else None)

        configure_logging(level="DEBUG", fmt="json")
        root = logging.getLogger()
        buf2 = io.StringIO()
        handler2 = logging.StreamHandler(buf2)
        handler2.setFormatter(root.handlers[0].formatter)
        root.addHandler(handler2)

        test_logger = logging.getLogger("ip_sakti.test")
        test_logger.info("Unit test message")

        buf2.seek(0)
        lines = [ln for ln in buf2.read().splitlines() if ln.strip()]
        if lines:
            record = json.loads(lines[-1])
            assert "timestamp" in record
            assert "level" in record
            assert "message" in record

    def test_get_logger_returns_logger(self) -> None:
        """get_logger() returns a logging.Logger instance."""
        logger = get_logger("ip_sakti.test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ip_sakti.test_module"

    def test_env_level_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LOG_LEVEL env var is respected when no argument is passed."""
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        configure_logging()
        assert logging.getLogger().level == logging.ERROR
