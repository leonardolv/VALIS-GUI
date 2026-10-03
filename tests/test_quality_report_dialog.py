"""Tests for QualityReportDialog accessibility, copy action, hand cursors, and headless safety."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pandas")
import pandas as pd
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.quality_report import QualityReportDialog


def test_quality_report_dialog_accessibility_and_tooltips(qtbot):
    df = pd.DataFrame(
        {
            "filename": ["slide_01.ndpi", "slide_02.ndpi"],
            "mean_d_tform": [1.2, 0.8],
            "mean_d_non_rigid": [0.3, 0.2],
        }
    )
    dialog = QualityReportDialog(df)
    qtbot.addWidget(dialog)

    # Table accessibility
    assert dialog._table.accessibleName() == "Alignment Quality Metrics Table"
    assert "metrics" in dialog._table.accessibleDescription().lower()

    # Copy table button
    assert dialog._copy_table_btn.accessibleName() == "Copy Quality Report Table to Clipboard"
    assert "copy" in dialog._copy_table_btn.toolTip().lower()
    assert dialog._copy_table_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    # Export CSV button
    assert dialog._export_csv_btn.accessibleName() == "Export Quality Report to CSV"
    assert "export" in dialog._export_csv_btn.toolTip().lower()
    assert dialog._export_csv_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    # Close button
    assert dialog._close_btn is not None
    assert dialog._close_btn.accessibleName() == "Close Quality Report Dialog"
    assert "close" in dialog._close_btn.toolTip().lower()
    assert dialog._close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_quality_report_dialog_copy_table_action_and_feedback(qtbot):
    df = pd.DataFrame(
        {
            "filename": ["slide_A.svs"],
            "mean_d_tform": [0.75],
        }
    )
    dialog = QualityReportDialog(df)
    qtbot.addWidget(dialog)

    # Click copy table button
    dialog._copy_table_btn.click()
    clipboard_text = QtWidgets.QApplication.clipboard().text()
    assert "slide_A.svs" in clipboard_text
    assert "mean_d_tform" in clipboard_text
    assert dialog._copy_table_btn.text() == "✓ Copied!"

    # Restore feedback
    dialog._restore_copy_btn_text()
    assert dialog._copy_table_btn.text() == "Copy Table"


def test_quality_report_dialog_export_csv_headless(qtbot, tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "filename": ["slide_01.ndpi"],
            "mean_d_tform": [1.5],
        }
    )
    dialog = QualityReportDialog(df)
    qtbot.addWidget(dialog)

    target_csv = tmp_path / "test_report.csv"
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(target_csv), "CSV Files (*.csv)"),
    )

    # Export CSV in headless mode
    dialog._export_csv_btn.click()
    assert target_csv.exists()
    content = target_csv.read_text(encoding="utf-8")
    assert "slide_01.ndpi" in content
