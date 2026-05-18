# tests/tracking/test_logger.py
"""Unit tests for infrastructure.tracking.logger.

Coverage targets
----------------
- configure_logging() silences mne and moabb to WARNING.
- configure_logging() is idempotent across repeated calls.
- renderer="json" selects JSONRenderer without raising.
- log_level="DEBUG" propagates to stdlib root logger.
"""

from __future__ import annotations

import logging

import structlog

from bci_calib.infrastructure.tracking.logger import configure_logging


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_silences_mne(self) -> None:
        """mne logger must be at WARNING or above after configuration."""
        configure_logging()
        assert logging.getLogger("mne").level == logging.WARNING

    def test_silences_moabb(self) -> None:
        """moabb logger must be at WARNING or above after configuration."""
        configure_logging()
        assert logging.getLogger("moabb").level == logging.WARNING

    def test_debug_level_propagates_to_stdlib(self) -> None:
        """Passing log_level='DEBUG' must lower the root stdlib logger."""
        configure_logging(log_level="DEBUG")
        root_level = logging.getLogger().level
        assert root_level <= logging.DEBUG

    def test_json_renderer_does_not_raise(self) -> None:
        """renderer='json' must complete without exception."""
        configure_logging(renderer="json")

    def test_console_renderer_does_not_raise(self) -> None:
        """renderer='console' must complete without exception."""
        configure_logging(renderer="console")

    def test_idempotent_on_repeated_calls(self) -> None:
        """Multiple successive calls must not raise or corrupt state."""
        configure_logging()
        configure_logging()
        configure_logging(renderer="json")
        configure_logging(log_level="WARNING")

    def test_structlog_get_logger_works_after_configuration(self) -> None:
        """get_logger() must return a usable logger after configuration."""
        configure_logging()
        log = structlog.get_logger("test.probe")
        # Should not raise; info() returns None on PrintLoggerFactory
        log.info("probe_event", key="value")
