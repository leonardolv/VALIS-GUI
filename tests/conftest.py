import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _restore_valis_logging_propagation():
    """Ensure valis_workstation logger propagates to root during tests so caplog functions reliably."""
    valis_logger = logging.getLogger("valis_workstation")
    prev_propagate = valis_logger.propagate
    valis_logger.propagate = True
    try:
        yield
    finally:
        valis_logger.propagate = prev_propagate


@pytest.fixture(autouse=True)
def _non_interactive_qt_dialogs(monkeypatch):
    """Force Qt dialog/file APIs to be non-blocking for all tests."""
    try:
        from PySide6 import QtWidgets
    except Exception:
        return

    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **kw: ""),
    )
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: ("", "")),
    )
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *a, **kw: ("", "")),
    )

    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "warning",
        staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "information",
        staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "about",
        staticmethod(lambda *a, **kw: None),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "question",
        staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.No),
    )

    monkeypatch.setattr(
        QtWidgets.QDialog,
        "exec",
        lambda self: QtWidgets.QDialog.DialogCode.Rejected,
    )
