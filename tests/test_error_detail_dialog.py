"""Tests for ErrorDetailDialog accessibility, tooltips, hand cursors, clipboard copy, and headless safety."""

from __future__ import annotations

import os
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.error_detail_dialog import (
    ErrorDetailDialog,
    show_error_dialog,
)


def test_error_detail_dialog_accessibility_and_tooltips(qtbot):
    dialog = ErrorDetailDialog(
        error_message="Sample registration error",
        technical_details="Traceback (most recent call last):\n  File ...",
        log_excerpt="2026-10-02 INFO Step 1\n2026-10-02 ERROR Step 2",
    )
    qtbot.addWidget(dialog)

    # Check button attributes
    assert dialog.copy_btn.accessibleName() == "Copy Error Details to Clipboard"
    assert dialog.copy_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "clipboard" in dialog.copy_btn.toolTip().lower()

    assert dialog.report_btn.accessibleName() == "Report Issue on GitHub"
    assert dialog.report_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "github" in dialog.report_btn.toolTip().lower()

    assert dialog.close_btn.accessibleName() == "Close Error Details Dialog"
    assert dialog.close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "close" in dialog.close_btn.toolTip().lower()

    # Check details group
    assert dialog.details_group is not None
    assert dialog.details_group.accessibleName() == "Technical Details Collapsible Group"
    assert dialog.details_group.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.details_text is not None
    assert dialog.details_text.accessibleName() == "Technical Error Details and Log Excerpt"


def test_error_detail_dialog_copy_action(qtbot):
    dialog = ErrorDetailDialog(
        error_message="Test message",
        technical_details="Traceback details",
        log_excerpt="Log lines",
    )
    qtbot.addWidget(dialog)

    dialog.copy_btn.click()
    assert dialog.copy_btn.text() == "✓ Copied!"
    clipboard_text = QtWidgets.QApplication.clipboard().text()
    assert "Test message" in clipboard_text
    assert "Traceback details" in clipboard_text
    assert "Log lines" in clipboard_text


def test_error_detail_dialog_report_issue_headless_safety(qtbot):
    dialog = ErrorDetailDialog(
        error_message="Test message",
    )
    qtbot.addWidget(dialog)
    # Under offscreen / pytest mode, report_btn click should return safely without browser popup
    dialog.report_btn.click()


def test_show_error_dialog_headless_safety(qtbot, tmp_path):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\nline 2\n", encoding="utf-8")

    # show_error_dialog should not block in offscreen / pytest environment
    show_error_dialog(
        parent,
        error_message="Headless error message",
        exception=RuntimeError("Test exception"),
        log_file=log_file,
    )
