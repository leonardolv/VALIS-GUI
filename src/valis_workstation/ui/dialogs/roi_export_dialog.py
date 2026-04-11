"""Export ROI specific cropped areas dialog."""

from __future__ import annotations

from PySide6 import QtWidgets

from valis_workstation.constants import ImageFormats


class ROIExportDialog(QtWidgets.QDialog):
    """Dialog for exporting a specific ROI bounded box to TIFF."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export ROI Crop")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(
            "Export bounded regions of interest to high-res OME-TIFF."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Basic form
        form = QtWidgets.QFormLayout()

        self._x = QtWidgets.QSpinBox()
        self._x.setRange(0, 1_000_000)
        form.addRow("X Coordinate (px):", self._x)

        self._y = QtWidgets.QSpinBox()
        self._y.setRange(0, 1_000_000)
        form.addRow("Y Coordinate (px):", self._y)

        self._width = QtWidgets.QSpinBox()
        self._width.setRange(10, 100_000)
        self._width.setValue(1000)
        form.addRow("Width (px):", self._width)

        self._height = QtWidgets.QSpinBox()
        self._height.setRange(10, 100_000)
        self._height.setValue(1000)
        form.addRow("Height (px):", self._height)

        self._format = QtWidgets.QComboBox()
        self._format.addItems(
            [ImageFormats.OME_TIFF, ImageFormats.TIFF, ImageFormats.PNG]
        )
        self._format.setCurrentText(ImageFormats.OME_TIFF)
        form.addRow("Format:", self._format)

        self._reopen = QtWidgets.QCheckBox()
        self._reopen.setChecked(True)
        form.addRow("Reopen in Viewer:", self._reopen)

        layout.addLayout(form)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

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
