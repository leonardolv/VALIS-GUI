"""Tests for DiagnosticsDialog usability, accessibility, and clipboard interaction."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
from valis_workstation.ui.dialogs.diagnostics_dialog import DiagnosticsDialog


def test_diagnostics_dialog_initialization_and_accessibility(qtbot, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "logs").mkdir()
    log_file = repo_root / "logs" / "valis_workstation.log"
    log_file.write_text("sample log", encoding="utf-8")

    last_result = {
        "output_dir": "/path/to/output",
        "registered_dir": "/path/to/registered",
    }

    dialog = DiagnosticsDialog(repo_root=repo_root, last_result=last_result)
    qtbot.addWidget(dialog)

    # Accessibility attributes
    assert dialog._text.accessibleName() == "Diagnostics Output"
    assert dialog._refresh_btn.accessibleName() == "Refresh Diagnostics"
    assert dialog._copy_btn.accessibleName() == "Copy Diagnostics to Clipboard"
    assert dialog._close_btn.accessibleName() == "Close Diagnostics"

    # Tooltips
    assert dialog._text.toolTip() == "System environment and runtime diagnostics log"
    assert dialog._refresh_btn.toolTip() == "Reload system and workstation runtime diagnostics"
    assert dialog._copy_btn.toolTip() == "Copy complete diagnostics report to system clipboard"
    assert dialog._close_btn.toolTip() == "Close the diagnostics dialog"

    # Cursors
    assert dialog._refresh_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._copy_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    # Content
    content = dialog._text.toPlainText()
    assert "VALIS Workstation Diagnostics" in content
    assert "Python:" in content
    assert "Platform:" in content
    assert "Qt:" in content
    assert str(repo_root) in content
    assert "/path/to/output" in content
    assert "/path/to/registered" in content
    assert "Log file exists: True" in content


def test_diagnostics_dialog_copy_to_clipboard(qtbot, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    dialog = DiagnosticsDialog(repo_root=repo_root)
    qtbot.addWidget(dialog)

    content = dialog._text.toPlainText()
    assert len(content) > 0

    dialog._copy_btn.click()
    clipboard_text = QtWidgets.QApplication.clipboard().text()
    assert clipboard_text == content
    assert dialog._copy_btn.text() == "✓ Copied!"


def test_diagnostics_dialog_refresh(qtbot, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    dialog = DiagnosticsDialog(repo_root=repo_root)
    qtbot.addWidget(dialog)

    dialog._text.setPlainText("cleared")
    assert dialog._text.toPlainText() == "cleared"

    dialog._refresh_btn.click()
    assert "VALIS Workstation Diagnostics" in dialog._text.toPlainText()


def test_copy_button_label_survives_a_double_click(qtbot, tmp_path):
    """A second click inside the feedback window must not freeze "Copied!"."""
    dialog = DiagnosticsDialog(repo_root=tmp_path)
    qtbot.addWidget(dialog)
    dialog._copy_btn.click()
    dialog._copy_btn.click()
    assert dialog._copy_btn.text() == "✓ Copied!"
    qtbot.waitUntil(lambda: dialog._copy_btn.text() == "Copy to Clipboard", timeout=4000)

def test_diagnostics_dialog_properties_and_query_helpers(qtbot, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "logs").mkdir()
    log_file = repo_root / "logs" / "valis_workstation.log"
    log_file.write_text("test log", encoding="utf-8")

    last_result = {
        "output_dir": "/output",
        "registered_dir": "/registered",
    }

    dialog = DiagnosticsDialog(repo_root=repo_root, last_result=last_result)
    qtbot.addWidget(dialog)

    # Properties
    assert dialog.text_edit == dialog._text
    assert dialog.refresh_button == dialog._refresh_btn
    assert dialog.copy_button == dialog._copy_btn
    assert dialog.close_button == dialog._close_btn

    # Query helpers
    assert dialog.has_diagnostics_content() is True
    assert "VALIS Workstation Diagnostics" in dialog.diagnostics_text()
    assert "/output" in dialog.diagnostics_text()
    assert dialog.is_copy_enabled() is True
    assert dialog.is_refresh_enabled() is True

    # Trigger copy
    dialog.trigger_copy()
    assert QtWidgets.QApplication.clipboard().text() == dialog.diagnostics_text()
    assert dialog.copy_button.text() == "✓ Copied!"

    # Clear and trigger refresh
    dialog.text_edit.setPlainText("")
    assert dialog.has_diagnostics_content() is False
    assert dialog.diagnostics_text() == ""
    dialog.trigger_refresh()
    assert dialog.has_diagnostics_content() is True
    assert "VALIS Workstation Diagnostics" in dialog.diagnostics_text()

