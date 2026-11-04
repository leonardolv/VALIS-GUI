"""Export ROI specific cropped areas dialog."""

from __future__ import annotations

import json

from PySide6 import QtCore, QtWidgets

from valis_workstation.constants import ImageFormats


class ROIExportDialog(QtWidgets.QDialog):
    """Dialog for exporting a specific ROI bounded box to TIFF."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("roiExportDialog")
        self.setAccessibleName("ROI Export Dialog")
        self.setWindowTitle("Export ROI Crop")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(
            "Export bounded regions of interest to high-res OME-TIFF."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Basic form
        form = QtWidgets.QFormLayout()

        self._x = QtWidgets.QSpinBox()
        self._x.setObjectName("roiXCoordSpin")
        self._x.setRange(0, 1_000_000)
        self._x.setAccessibleName("X Coordinate Pixels")
        self._x.setToolTip("Top-left corner of the ROI in the registered coordinate space (pixels)")
        form.addRow("X Coordinate (px):", self._x)

        self._y = QtWidgets.QSpinBox()
        self._y.setObjectName("roiYCoordSpin")
        self._y.setRange(0, 1_000_000)
        self._y.setAccessibleName("Y Coordinate Pixels")
        self._y.setToolTip("Top-left corner of the ROI in the registered coordinate space (pixels)")
        form.addRow("Y Coordinate (px):", self._y)

        self._width = QtWidgets.QSpinBox()
        self._width.setObjectName("roiWidthSpin")
        self._width.setRange(10, 100_000)
        self._width.setValue(1000)
        self._width.setAccessibleName("Width Pixels")
        self._width.setToolTip("Size of the ROI region to export (pixels in registered space)")
        form.addRow("Width (px):", self._width)

        self._height = QtWidgets.QSpinBox()
        self._height.setObjectName("roiHeightSpin")
        self._height.setRange(10, 100_000)
        self._height.setValue(1000)
        self._height.setAccessibleName("Height Pixels")
        self._height.setToolTip("Size of the ROI region to export (pixels in registered space)")
        form.addRow("Height (px):", self._height)

        self._format = QtWidgets.QComboBox()
        self._format.setObjectName("roiFormatCombo")
        self._format.addItems(
            [ImageFormats.OME_TIFF, ImageFormats.TIFF, ImageFormats.PNG]
        )
        self._format.setCurrentText(ImageFormats.OME_TIFF)
        self._format.setAccessibleName("Export Image Format")
        self._format.setToolTip("Image format for exported cropped slides")
        self._format.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        form.addRow("Format:", self._format)

        self._reopen = QtWidgets.QCheckBox()
        self._reopen.setObjectName("roiReopenCheck")
        self._reopen.setChecked(True)
        self._reopen.setAccessibleName("Reopen in Viewer")
        self._reopen.setToolTip("Automatically reopen exported crops in the viewer")
        self._reopen.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        form.addRow("Reopen in Viewer:", self._reopen)

        layout.addLayout(form)

        # Status / Feedback label for non-blocking feedback
        self._feedback_label = QtWidgets.QLabel("")
        self._feedback_label.setObjectName("roiFeedbackLabel")
        self._feedback_label.setAccessibleName("Clipboard and Validation Feedback")
        self._feedback_label.setWordWrap(True)
        layout.addWidget(self._feedback_label)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.copy_json_btn = QtWidgets.QPushButton("Copy as JSON")
        self.copy_json_btn.setObjectName("roiCopyJsonBtn")
        self.copy_json_btn.setAccessibleName("Copy Coordinates as JSON")
        self.copy_json_btn.setToolTip("Copy ROI bounding box coordinates to clipboard as JSON")
        self.copy_json_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.copy_json_btn.clicked.connect(self._copy_as_json)
        button_layout.addWidget(self.copy_json_btn)

        self.paste_json_btn = QtWidgets.QPushButton("Paste from JSON")
        self.paste_json_btn.setObjectName("roiPasteJsonBtn")
        self.paste_json_btn.setAccessibleName("Paste Coordinates from JSON")
        self.paste_json_btn.setToolTip("Paste and populate ROI coordinates from JSON in clipboard")
        self.paste_json_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.paste_json_btn.clicked.connect(self._paste_from_json)
        button_layout.addWidget(self.paste_json_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        # OK/Cancel/Reset on their own row so a narrow dialog cannot clip them.
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Reset
        )
        btns.setObjectName("roiButtonBox")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.reset_button = btns.button(QtWidgets.QDialogButtonBox.StandardButton.Reset)
        if self.reset_button is not None:
            self.reset_button.setObjectName("roiResetBtn")
            self.reset_button.setAccessibleName("Reset to Defaults")
            self.reset_button.setToolTip("Reset ROI coordinates and export options to defaults")
            self.reset_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.reset_button.clicked.connect(self._reset_defaults)

        self.ok_button = btns.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if self.ok_button is not None:
            self.ok_button.setObjectName("roiOkBtn")
            self.ok_button.setAccessibleName("Export ROI Crop")
            self.ok_button.setToolTip("Export the selected ROI crop with specified dimensions and format")
            self.ok_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self.cancel_button = btns.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setObjectName("roiCancelBtn")
            self.cancel_button.setAccessibleName("Cancel")
            self.cancel_button.setToolTip("Close dialog without exporting")
            self.cancel_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        button_layout.addWidget(btns)
        layout.addLayout(button_layout)

    def _copy_as_json(self) -> None:
        """Copy ROI coordinates as JSON to clipboard with non-blocking feedback."""
        data = {
            "x": self._x.value(),
            "y": self._y.value(),
            "width": self._width.value(),
            "height": self._height.value(),
            "format": self._format.currentText(),
        }
        json_str = json.dumps(data, indent=2)
        QtWidgets.QApplication.clipboard().setText(json_str)
        self._feedback_label.setText("✓ Copied ROI bounding box to clipboard as JSON")
        self._feedback_label.setStyleSheet("color: #4CAF50;")

    def _paste_from_json(self) -> None:
        """Paste ROI coordinates from clipboard JSON."""
        text = QtWidgets.QApplication.clipboard().text().strip()
        if not text:
            self._feedback_label.setText("⚠ Clipboard is empty")
            self._feedback_label.setStyleSheet("color: #F44336;")
            return
        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object with coordinates")
            # Validate every field first so a bad value cannot leave the
            # dialog half-updated; bools are not coordinates.
            spins = {
                "x": self._x,
                "y": self._y,
                "width": self._width,
                "height": self._height,
            }
            pending: dict[str, int] = {}
            for key in spins:
                if key not in data:
                    continue
                val = data[key]
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    raise ValueError(f"'{key}' must be a number")
                if val != val or val in (float("inf"), float("-inf")):
                    raise ValueError(f"'{key}' must be finite")
                lo, hi = spins[key].minimum(), spins[key].maximum()
                if not lo <= val <= hi:
                    raise ValueError(f"'{key}' must be between {lo} and {hi}")
                pending[key] = int(val)
            for key, val in pending.items():
                spins[key].setValue(val)
            updated = bool(pending)
            if "format" in data and str(data["format"]) in [
                ImageFormats.OME_TIFF,
                ImageFormats.TIFF,
                ImageFormats.PNG,
            ]:
                self._format.setCurrentText(str(data["format"]))
            if updated:
                self._feedback_label.setText("✓ Loaded ROI coordinates from clipboard JSON")
                self._feedback_label.setStyleSheet("color: #4CAF50;")
            else:
                self._feedback_label.setText("⚠ JSON missing 'x', 'y', 'width', or 'height'")
                self._feedback_label.setStyleSheet("color: #F44336;")
        except Exception as e:
            self._feedback_label.setText(f"⚠ Invalid ROI JSON: {e}")
            self._feedback_label.setStyleSheet("color: #F44336;")

    def _reset_defaults(self) -> None:
        """Reset coordinates and export choices to default values."""
        self._x.setValue(0)
        self._y.setValue(0)
        self._width.setValue(1000)
        self._height.setValue(1000)
        self._format.setCurrentText(ImageFormats.OME_TIFF)
        self._reopen.setChecked(True)
        self._feedback_label.setText("✓ Reset coordinates and options to defaults")
        self._feedback_label.setStyleSheet("color: #4CAF50;")

    def get_options(self) -> dict:
        """Returns the configured bounding box and format options."""
        return {
            "bbox": (
                self._x.value(),
                self._y.value(),
                self._width.value(),
                self._height.value(),
            ),
            "format": self._format.currentText(),
            "reopen": self._reopen.isChecked(),
        }

