"""
Unit tests for ErrorDetailDialog and DiagnosticsDialog.
Verifies accessible names, object names, button tooltips, and pointer cursors.
"""
from pathlib import Path
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.error_detail_dialog import ErrorDetailDialog
from valis_workstation.ui.dialogs.diagnostics_dialog import DiagnosticsDialog


def test_error_detail_dialog_accessibility(qapp):
    dlg = ErrorDetailDialog(
        error_message="Something failed",
        technical_details="Traceback (most recent call last):\nValueError: invalid input",
        log_excerpt="[INFO] Starting task\n[ERROR] Task aborted",
    )
    try:
        assert dlg.objectName() == "errorDetailDialog"
        assert dlg.accessibleName() == "Error Details Dialog"

        assert dlg.message_label.objectName() == "errorMessageLabel"
        assert dlg.error_text.objectName() == "errorTextLabel"
        assert dlg.error_text.accessibleName() == "Error message"

        assert dlg.details_group is not None
        assert dlg.details_group.objectName() == "errorDetailsGroup"
        assert dlg.details_group.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dlg.details_text is not None
        assert dlg.details_text.objectName() == "errorDetailsText"

        assert dlg.copy_btn.objectName() == "errorCopyBtn"
        assert dlg.copy_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dlg.copy_btn.toolTip()) > 0

        assert dlg.report_btn.objectName() == "errorReportBtn"
        assert dlg.report_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dlg.report_btn.toolTip()) > 0

        assert dlg.close_btn.objectName() == "errorCloseBtn"
        assert dlg.close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dlg.close_btn.toolTip()) > 0

        # Test non-blocking copy feedback
        dlg._copy_to_clipboard("test", "tech", "log")
        assert dlg.copy_btn.text() == "✓ Copied!"
    finally:
        dlg.close()


def test_diagnostics_dialog_accessibility(qapp, tmp_path):
    dlg = DiagnosticsDialog(repo_root=tmp_path)
    try:
        assert dlg.objectName() == "diagnosticsDialog"
        assert dlg.accessibleName() == "Diagnostics Dialog"

        assert dlg._text.objectName() == "diagnosticsText"

        for btn in (dlg._refresh_btn, dlg._copy_btn, dlg._close_btn):
            assert btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
            assert len(btn.toolTip()) > 0
            assert len(btn.accessibleName()) > 0

        assert dlg._refresh_btn.objectName() == "diagnosticsRefreshBtn"
        assert dlg._copy_btn.objectName() == "diagnosticsCopyBtn"
        assert dlg._close_btn.objectName() == "diagnosticsCloseBtn"

        # Test non-blocking copy feedback
        dlg._copy_to_clipboard()
        assert dlg._copy_btn.text() == "✓ Copied!"
    finally:
        dlg.close()
