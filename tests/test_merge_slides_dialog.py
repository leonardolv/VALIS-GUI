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

# Dialog and group metadata
    assert dialog.objectName() == "mergeSlidesDialog"
    assert dialog.accessibleName() == "Merge Slides Dialog"
    assert "channel mapping" in dialog.accessibleDescription().lower()
    assert dialog.findChild(QtWidgets.QLabel, "mergeInfoBanner") is not None
    assert dialog.findChild(QtWidgets.QGroupBox, "channelMappingGroup") is not None
    assert dialog.findChild(QtWidgets.QGroupBox, "mergeOptionsGroup") is not None

    # Public widget property accessors
    assert dialog.table is dialog._table
    assert dialog.button_box is dialog._button_box
    assert dialog.select_all_button is dialog._select_all_btn
    assert dialog.select_none_button is dialog._select_none_btn
    assert dialog.export_config_button is dialog._export_config_btn
    assert dialog.ok_button is dialog._ok_btn
    assert dialog.cancel_button is dialog._cancel_btn
    assert dialog.duplicate_handling_combo is dialog._duplicate_handling
    assert dialog.output_name_edit is dialog._output_name
    assert dialog.normalize_checkbox is dialog._normalize

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

    # Selection query helpers
    assert dialog.included_slide_count() == 2
    assert dialog.is_all_selected() is True
    assert dialog.is_none_selected() is False
    assert dialog.selected_slide_names() == ["Slide_1", "Slide_2"]

    # Click Select None
    dialog._select_none_btn.click()
    for i in range(2):
        cb = dialog._table.cellWidget(i, 0)
        assert cb.isChecked() is False
    assert dialog.included_slide_count() == 0
    assert dialog.is_all_selected() is False
    assert dialog.is_none_selected() is True
    assert dialog.selected_slide_names() == []

    # Click Select All
    dialog._select_all_btn.click()
    for i in range(2):
        cb = dialog._table.cellWidget(i, 0)
        assert cb.isChecked() is True
    assert dialog.included_slide_count() == 2
    assert dialog.is_all_selected() is True
    assert dialog.is_none_selected() is False
    assert dialog.selected_slide_names() == ["Slide_1", "Slide_2"]


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


def test_name_columns_stretch_to_fill_the_table(qtbot):
    from PySide6 import QtWidgets

    from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog

    dlg = MergeSlidesDialog(["a_very_long_slide_name_stain_01.ndpi", "b.tif"])
    qtbot.addWidget(dlg)
    header = dlg.table.horizontalHeader()
    stretch = QtWidgets.QHeaderView.ResizeMode.Stretch
    assert header.sectionResizeMode(1) == stretch
    assert header.sectionResizeMode(2) == stretch


def test_merge_slides_dialog_ergonomics_helpers_and_action_triggers(qtbot, tmp_path, monkeypatch):
    """Test MergeSlidesDialog ergonomic setters, row queries, and action triggers."""
    slides = ["Slide_DAPI", "Slide_GFP", "Slide_RFP"]
    dialog = MergeSlidesDialog(slides)
    qtbot.addWidget(dialog)

    # 1. Output image name
    assert dialog.output_image_name() == "merged_image"
    dialog.set_output_image_name("multiplex_panel_1")
    assert dialog.output_image_name() == "multiplex_panel_1"

    # 2. Overlap / duplicate handling
    assert dialog.duplicate_handling() == "Average"
    assert dialog.set_duplicate_handling("Maximum") is True
    assert dialog.duplicate_handling() == "Maximum"
    assert dialog.set_duplicate_handling("InvalidMethod") is False

    # 3. Intensity normalization
    assert dialog.is_normalize_enabled() is True
    dialog.set_normalize(False)
    assert dialog.is_normalize_enabled() is False
    dialog.set_normalize(True)
    assert dialog.is_normalize_enabled() is True

    # 4. Row lookups and slide inclusion
    assert dialog.slide_row_index("Slide_DAPI") == 0
    assert dialog.slide_row_index("Slide_GFP") == 1
    assert dialog.slide_row_index("Nonexistent") == -1

    assert dialog.is_slide_included("Slide_DAPI") is True
    assert dialog.is_slide_included("Nonexistent") is False
    assert dialog.set_slide_included("Slide_DAPI", False) is True
    assert dialog.is_slide_included("Slide_DAPI") is False
    assert dialog.set_slide_included("Nonexistent", True) is False
    assert dialog.set_slide_included("Slide_DAPI", True) is True
    assert dialog.is_slide_included("Slide_DAPI") is True

    # 5. Channel names and colors
    assert dialog.channel_name("Slide_DAPI") == "Channel_1"
    assert dialog.channel_name("Nonexistent") is None
    assert dialog.set_channel_name("Slide_DAPI", "DAPI_405") is True
    assert dialog.channel_name("Slide_DAPI") == "DAPI_405"
    assert dialog.set_channel_name("Nonexistent", "Foo") is False

    assert dialog.channel_color("Slide_GFP") == "Auto"
    assert dialog.channel_color("Nonexistent") is None
    assert dialog.set_channel_color("Slide_GFP", "Green") is True
    assert dialog.channel_color("Slide_GFP") == "Green"
    assert dialog.set_channel_color("Slide_GFP", "InvalidColor") is False
    assert dialog.set_channel_color("Nonexistent", "Red") is False

    # 6. Action triggers: select none / select all
    dialog.trigger_select_none()
    assert dialog.is_none_selected() is True
    assert dialog.included_slide_count() == 0

    dialog.trigger_select_all()
    assert dialog.is_all_selected() is True
    assert dialog.included_slide_count() == 3

    # 7. Action trigger: export config
    export_path = tmp_path / "trigger_export_cfg.json"
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(export_path), "JSON Files (*.json)"),
    )
    dialog.trigger_export_config()
    assert export_path.exists()
    cfg = json.loads(export_path.read_text(encoding="utf-8"))
    assert cfg["output_name"] == "multiplex_panel_1"
    assert cfg["duplicate_handling"] == "maximum"

    # 8. Action triggers: accept and reject
    accepted = []
    rejected = []
    dialog.accepted.connect(lambda: accepted.append(True))
    dialog.rejected.connect(lambda: rejected.append(True))

    dialog.trigger_accept()
    assert len(accepted) == 1

    dialog.trigger_reject()
    assert len(rejected) == 1
