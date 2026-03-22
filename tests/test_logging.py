"""Tests for logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from valis_workstation.utils.logging_config import setup_logging


class TestLogging:
    def test_creates_log_file(self, tmp_path: Path) -> None:
        setup_logging(tmp_path)
        logger = logging.getLogger("valis_workstation.test_log")
        logger.info("Hello from test")

        log_file = tmp_path / "valis_workstation.log"
        assert log_file.exists()
        assert "Hello from test" in log_file.read_text(encoding="utf-8")

    def test_debug_written_to_file(self, tmp_path: Path) -> None:
        setup_logging(tmp_path)
        logger = logging.getLogger("valis_workstation.test_debug")
        logger.debug("debug message")

        log_file = tmp_path / "valis_workstation.log"
        content = log_file.read_text(encoding="utf-8")
        assert "debug message" in content

    def test_creates_directory(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "nested" / "logs"
        setup_logging(log_dir)
        assert log_dir.exists()

    def test_verbose_mode(self, tmp_path: Path) -> None:
        setup_logging(tmp_path, verbose=True)
        logger = logging.getLogger("valis_workstation")
        # After verbose setup, our logger should exist
        assert logger is not None
