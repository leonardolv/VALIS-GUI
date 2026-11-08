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


def test_quality_report_dialog_properties_and_ergonomics(qtbot):
    df = pd.DataFrame(
        {
            "filename": ["slide_01.ndpi", "slide_02.ndpi"],
            "mean_d_tform": [1.25, 0.95],
            "mean_d_non_rigid": [0.35, 0.15],
        }
    )
    dialog = QualityReportDialog(df)
    qtbot.addWidget(dialog)

    # Dialog metadata
    assert dialog.objectName() == "qualityReportDialog"
    assert dialog.accessibleName() == "Alignment Quality Report Dialog"

    # Properties
    assert dialog.table is dialog._table
    assert dialog.copy_table_button is dialog._copy_table_btn
    assert dialog.export_csv_button is dialog._export_csv_btn
    assert dialog.close_button is dialog._close_btn

    # Ergonomic queries
    assert dialog.row_count() == 2
    assert dialog.column_count() == 3
    assert dialog.has_data() is True
    assert dialog.headers() == ["filename", "mean_d_tform", "mean_d_non_rigid"]
    assert dialog.cell_text(0, 0) == "slide_01.ndpi"
    assert dialog.cell_text(0, 1) == "1.25"
    assert dialog.cell_text(1, 0) == "slide_02.ndpi"

    # Copy trigger
    dialog.trigger_copy_table()
    clipboard_text = QtWidgets.QApplication.clipboard().text()
    assert "slide_01.ndpi" in clipboard_text
    assert "slide_02.ndpi" in clipboard_text

    # Close trigger
    dialog.trigger_close()


def test_quality_report_dialog_empty_state_queries(qtbot):
    empty_df = pd.DataFrame()
    dialog = QualityReportDialog(empty_df)
    qtbot.addWidget(dialog)

    assert dialog.row_count() == 0
    assert dialog.column_count() == 0
    assert dialog.has_data() is False
    assert dialog.headers() == []
    assert dialog.cell_text(0, 0) == ""
