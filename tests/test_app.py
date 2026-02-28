"""Tests for valis_workstation.app utility functions.

Covers _load_stylesheet, _simple_elastix_available, _start_jvm,
_shutdown_jvm, and _install_excepthook — all unit-testable in isolation
with mocking.
"""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from valis_workstation.app import (
    _load_stylesheet,
    _simple_elastix_available,
    _start_jvm,
    _shutdown_jvm,
    _install_excepthook,
)


# ---------------------------------------------------------------------------
# _load_stylesheet
# ---------------------------------------------------------------------------

class TestLoadStylesheet:
    """Tests for stylesheet loading."""

    def test_returns_css_when_file_exists(self, tmp_path):
        """Returns the file contents when the QSS file exists."""
        style_dir = tmp_path / "src" / "valis_workstation" / "styles"
        style_dir.mkdir(parents=True)
        qss = style_dir / "adobe_dark.qss"
        qss.write_text("QWidget { color: red; }", encoding="utf-8")
        result = _load_stylesheet(tmp_path)
        assert "QWidget" in result

    def test_returns_empty_when_missing(self, tmp_path):
        """Returns empty string when the QSS file does not exist."""
        result = _load_stylesheet(tmp_path)
        assert result == ""


# ---------------------------------------------------------------------------
# _simple_elastix_available
# ---------------------------------------------------------------------------

class TestSimpleElastixAvailable:
    """Tests for SimpleElastix detection."""

    def test_true_when_elastix_filter_present(self):
        mock_sitk = MagicMock()
        mock_sitk.ElastixImageFilter = MagicMock()
        with patch.dict(sys.modules, {"SimpleITK": mock_sitk}):
            with patch("importlib.util.find_spec", return_value=True):
                assert _simple_elastix_available() is True

    def test_false_when_no_simpleitk(self):
        with patch("importlib.util.find_spec", return_value=None):
            assert _simple_elastix_available() is False

    def test_false_when_no_elastix_filter(self):
        mock_sitk = MagicMock(spec=[])  # no ElastixImageFilter attr
        with patch.dict(sys.modules, {"SimpleITK": mock_sitk}):
            with patch("importlib.util.find_spec", return_value=True):
                assert _simple_elastix_available() is False


# ---------------------------------------------------------------------------
# _start_jvm / _shutdown_jvm
# ---------------------------------------------------------------------------

class TestStartJvm:
    """Tests for JVM startup wrapper."""

    def test_returns_true_on_success(self):
        mock_scy = MagicMock()
        with patch.dict(sys.modules, {"scyjava": mock_scy}):
            with patch("importlib.util.find_spec", return_value=True):
                assert _start_jvm() is True
                mock_scy.start_jvm.assert_called_once()

    def test_returns_false_when_no_scyjava(self):
        with patch("importlib.util.find_spec", return_value=None):
            assert _start_jvm() is False

    def test_returns_false_on_exception(self):
        mock_scy = MagicMock()
        mock_scy.start_jvm.side_effect = RuntimeError("boom")
        with patch.dict(sys.modules, {"scyjava": mock_scy}):
            with patch("importlib.util.find_spec", return_value=True):
                assert _start_jvm() is False


class TestShutdownJvm:
    """Tests for JVM shutdown wrapper."""

    def test_calls_shutdown_when_available(self):
        mock_scy = MagicMock()
        with patch.dict(sys.modules, {"scyjava": mock_scy}):
            with patch("importlib.util.find_spec", return_value=True):
                _shutdown_jvm()
                mock_scy.shutdown_jvm.assert_called_once()

    def test_noop_when_no_scyjava(self):
        with patch("importlib.util.find_spec", return_value=None):
            _shutdown_jvm()  # should not raise

    def test_logs_exception_on_failure(self, caplog):
        mock_scy = MagicMock()
        mock_scy.shutdown_jvm.side_effect = RuntimeError("shutdown fail")
        with patch.dict(sys.modules, {"scyjava": mock_scy}):
            with patch("importlib.util.find_spec", return_value=True):
                with caplog.at_level(logging.ERROR):
                    _shutdown_jvm()
                assert "shutdown fail" in caplog.text or "Failed" in caplog.text


# ---------------------------------------------------------------------------
# _install_excepthook
# ---------------------------------------------------------------------------

class TestInstallExcepthook:
    """Tests for the global exception hook installer."""

    def test_replaces_sys_excepthook(self, qtbot):
        from PySide6 import QtWidgets
        app = QtWidgets.QApplication.instance()
        original = sys.excepthook
        _install_excepthook(app)
        assert sys.excepthook is not original
        # Restore
        sys.excepthook = original
