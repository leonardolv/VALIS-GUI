"""Tests for ROIExportDialog usability, accessibility, and JSON import/export."""

from __future__ import annotations

import json
import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
from valis_workstation.constants import ImageFormats
from valis_workstation.ui.dialogs.roi_export_dialog import ROIExportDialog


def test_roi_export_dialog_defaults_and_accessibility(qtbot):
    dialog = ROIExportDialog()
    qtbot.addWidget(dialog)

    assert dialog.objectName() == "roiExportDialog"
    assert dialog.accessibleName() == "ROI Export Dialog"

    assert dialog._x.objectName() == "roiXCoordSpin"
    assert dialog._x.accessibleName() == "X Coordinate Pixels"
    assert dialog._y.objectName() == "roiYCoordSpin"
    assert dialog._y.accessibleName() == "Y Coordinate Pixels"
    assert dialog._width.objectName() == "roiWidthSpin"
    assert dialog._width.accessibleName() == "Width Pixels"
    assert dialog._height.objectName() == "roiHeightSpin"
    assert dialog._height.accessibleName() == "Height Pixels"

    assert dialog._format.objectName() == "roiFormatCombo"
    assert dialog._format.accessibleName() == "Export Image Format"
    assert dialog._format.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog._reopen.objectName() == "roiReopenCheck"
    assert dialog._reopen.accessibleName() == "Reopen in Viewer"
    assert dialog._reopen.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.copy_json_btn.objectName() == "roiCopyJsonBtn"
    assert dialog.copy_json_btn.accessibleName() == "Copy Coordinates as JSON"
    assert dialog.copy_json_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.paste_json_btn.objectName() == "roiPasteJsonBtn"
    assert dialog.paste_json_btn.accessibleName() == "Paste Coordinates from JSON"
    assert dialog.paste_json_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.reset_button is not None
    assert dialog.reset_button.objectName() == "roiResetBtn"
    assert dialog.reset_button.accessibleName() == "Reset to Defaults"
    assert dialog.reset_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.ok_button is not None
    assert dialog.ok_button.objectName() == "roiOkBtn"
    assert dialog.ok_button.accessibleName() == "Export ROI Crop"
    assert dialog.ok_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dialog.cancel_button is not None
    assert dialog.cancel_button.objectName() == "roiCancelBtn"
    assert dialog.cancel_button.accessibleName() == "Cancel"
    assert dialog.cancel_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    options = dialog.get_options()
    assert options["bbox"] == (0, 0, 1000, 1000)
    assert options["format"] == ImageFormats.OME_TIFF
    assert options["reopen"] is True


def test_roi_export_dialog_copy_as_json(qtbot):
    dialog = ROIExportDialog()
    qtbot.addWidget(dialog)

    dialog._x.setValue(250)
    dialog._y.setValue(500)
    dialog._width.setValue(1200)
    dialog._height.setValue(800)
    dialog._format.setCurrentText(ImageFormats.PNG)

    dialog.copy_json_btn.click()

    assert "✓ Copied ROI bounding box" in dialog._feedback_label.text()
    clipboard_text = QtWidgets.QApplication.clipboard().text()
    data = json.loads(clipboard_text)
    assert data["x"] == 250
    assert data["y"] == 500
    assert data["width"] == 1200
    assert data["height"] == 800
    assert data["format"] == ImageFormats.PNG


def test_roi_export_dialog_paste_from_json(qtbot):
    dialog = ROIExportDialog()
    qtbot.addWidget(dialog)

    payload = {
        "x": 350,
        "y": 700,
        "width": 2048,
        "height": 1536,
        "format": ImageFormats.TIFF,
    }
    QtWidgets.QApplication.clipboard().setText(json.dumps(payload))

    dialog.paste_json_btn.click()

    assert "✓ Loaded ROI coordinates" in dialog._feedback_label.text()
    options = dialog.get_options()
    assert options["bbox"] == (350, 700, 2048, 1536)
    assert options["format"] == ImageFormats.TIFF


def test_roi_export_dialog_paste_invalid_json(qtbot):
    dialog = ROIExportDialog()
    qtbot.addWidget(dialog)

    QtWidgets.QApplication.clipboard().setText("not a json string")
    dialog.paste_json_btn.click()

    assert "⚠ Invalid ROI JSON" in dialog._feedback_label.text()


def test_roi_export_dialog_reset_to_defaults(qtbot):
    dialog = ROIExportDialog()
    qtbot.addWidget(dialog)

    dialog._x.setValue(999)
    dialog._y.setValue(888)
    dialog._width.setValue(5000)
    dialog._height.setValue(4000)
    dialog._format.setCurrentText(ImageFormats.TIFF)
    dialog._reopen.setChecked(False)

    dialog.reset_button.click()

    assert "✓ Reset coordinates" in dialog._feedback_label.text()
    options = dialog.get_options()
    assert options["bbox"] == (0, 0, 1000, 1000)
    assert options["format"] == ImageFormats.OME_TIFF
    assert options["reopen"] is True
