"""Tests for MergeSlidesDialog accessibility, tooltips, hand cursors, and headless safety."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

pytest.importorskip("PySide6")
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog


def test_merge_slides_dialog_accessibility_and_tooltips(qtbot):
    slides = ["Slide_DAPI", "Slide_GFP", "Slide_RFP"]
    dialog = MergeSlidesDialog(slides)
    qtbot.addWidget(dialog)

    # Table accessibility
    assert dialog._table.accessibleName() == "Channel Mapping Table"
    assert "channel" in dialog._table.accessibleDescription().lower()

    # Row cell widgets accessibility and cursors
    for i, name in enumerate(slides):
        cb = dialog._table.cellWidget(i, 0)
        assert isinstance(cb, QtWidgets.QCheckBox)
        assert name in cb.accessibleName()
        assert cb.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert cb.toolTip() != ""

        combo = dialog._table.cellWidget(i, 3)
        assert isinstance(combo, QtWidgets.QComboBox)
        assert name in combo.accessibleName()
        assert combo.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert combo.toolTip() != ""

    # Merge options accessibility and cursors
    assert dialog._duplicate_handling.accessibleName() == "Overlap handling method"
    assert dialog._duplicate_handling.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._duplicate_handling.toolTip() != ""

    assert dialog._output_name.accessibleName() == "Merged output image name"
    assert dialog._output_name.toolTip() != ""

    assert dialog._normalize.accessibleName() == "Normalize intensities across channels"
    assert dialog._normalize.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._normalize.toolTip() != ""

    # Utility and action buttons accessibility, tooltips, and cursors
    assert dialog._select_all_btn.accessibleName() == "Select all slides"
    assert dialog._select_all_btn.toolTip() != ""
    assert dialog._select_all_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog._select_none_btn.accessibleName() == "Deselect all slides"
    assert dialog._select_none_btn.toolTip() != ""
    assert dialog._select_none_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog._export_config_btn.accessibleName() == "Export channel configuration to JSON"
    assert dialog._export_config_btn.toolTip() != ""
    assert dialog._export_config_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog._ok_btn is not None
    assert dialog._ok_btn.accessibleName() != ""
    assert dialog._ok_btn.toolTip() != ""
    assert dialog._ok_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog._cancel_btn is not None
    assert dialog._cancel_btn.accessibleName() != ""
    assert dialog._cancel_btn.toolTip() != ""
    assert dialog._cancel_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_merge_slides_dialog_selection_toggle_actions(qtbot):
    slides = ["Slide_1", "Slide_2"]
    dialog = MergeSlidesDialog(slides)
    qtbot.addWidget(dialog)

    # Initial state: all selected
    for i in range(2):
        cb = dialog._table.cellWidget(i, 0)
        assert cb.isChecked() is True

    # Click Select None
    dialog._select_none_btn.click()
    for i in range(2):
        cb = dialog._table.cellWidget(i, 0)
        assert cb.isChecked() is False

    # Click Select All
    dialog._select_all_btn.click()
    for i in range(2):
        cb = dialog._table.cellWidget(i, 0)
        assert cb.isChecked() is True


def test_merge_slides_dialog_headless_export_config(qtbot, tmp_path, monkeypatch):
    slides = ["Slide_CY3", "Slide_CY5"]
    dialog = MergeSlidesDialog(slides)
    qtbot.addWidget(dialog)

    export_path = tmp_path / "test_merge_cfg.json"
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(export_path), "JSON Files (*.json)"),
    )

    # Trigger export config under headless test conditions
    dialog._export_config()
    assert export_path.exists()

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert "channels" in data
    assert len(data["channels"]) == 2
    assert data["output_name"] == "merged_image"
