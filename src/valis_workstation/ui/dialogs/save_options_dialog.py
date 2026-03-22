"""Dialog for configuring save/export options."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from valis_workstation.constants import ImageFormats


class SaveOptionsDialog(QtWidgets.QDialog):
    """Dialog for configuring image save options.

    Allows users to customize pyramid levels, compression, quality, and tile size
    for saved registered images.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)

        # Form layout for options
        form = QtWidgets.QFormLayout()

        # Pyramid levels
        self._pyramid_levels = QtWidgets.QSpinBox()
        self._pyramid_levels.setRange(1, 10)
        self._pyramid_levels.setValue(4)
        self._pyramid_levels.setToolTip(
            "Number of pyramid levels for multi-resolution images.\n"
            "More levels = better viewer performance but larger file size.\n"
            "Recommended: 4-6 for whole slide images."
        )
        form.addRow("Pyramid levels:", self._pyramid_levels)

        # Compression level
        self._compression = QtWidgets.QSpinBox()
        self._compression.setRange(0, 9)
        self._compression.setValue(1)
        self._compression.setToolTip(
            "PNG/TIFF compression level (0-9).\n"
            "0 = No compression (fastest, largest)\n"
            "1 = Fast compression (good balance)\n"
            "9 = Maximum compression (slowest, smallest)\n"
            "Recommended: 1 for speed, 5-6 for balanced, 9 for archival."
        )
        form.addRow("Compression (0-9):", self._compression)

        # Image quality (for JPEG)
        self._quality = QtWidgets.QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(95)
        self._quality.setToolTip(
            "JPEG quality (1-100).\n"
            "Higher = better quality but larger file size.\n"
            "Recommended: 90-95 for diagnostic quality, 80-85 for preview."
        )
        form.addRow("JPEG Quality (1-100):", self._quality)

        # Tile size
        self._tile_size = QtWidgets.QComboBox()
        self._tile_size.addItems(["128", "256", "512", "1024", "2048"])
        self._tile_size.setCurrentText("512")
        self._tile_size.setToolTip(
            "Tile size for tiled images (pixels).\n"
            "Smaller tiles = better for sparse viewing, more overhead.\n"
            "Larger tiles = better compression, faster processing.\n"
            "Recommended: 256-512 for web viewers, 1024 for local viewing."
        )
        form.addRow("Tile size:", self._tile_size)

        # Format selection
        self._format = QtWidgets.QComboBox()
        self._format.addItems(ImageFormats.all())
        self._format.setCurrentText(ImageFormats.OME_TIFF)
        self._format.setToolTip(
            "Output image format:\n"
            "• OME-TIFF: Standard for microscopy, preserves metadata\n"
            "• TIFF: General purpose, good compatibility\n"
            "• JPEG: Lossy compression, smallest files\n"
            "• PNG: Lossless, good for web/preview"
        )
        form.addRow("Format:", self._format)

        layout.addLayout(form)

        # Estimated file size info
        self._info_label = QtWidgets.QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #888; font-style: italic;")
        self._update_info()
        layout.addWidget(self._info_label)

        # Connect signals to update info
        self._pyramid_levels.valueChanged.connect(self._update_info)
        self._compression.valueChanged.connect(self._update_info)
        self._quality.valueChanged.connect(self._update_info)
        self._format.currentTextChanged.connect(self._update_info)

        # Dialog buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_info(self) -> None:
        """Update the info label with current settings summary."""
        format_name = self._format.currentText()
        compression = self._compression.value()
        quality = self._quality.value()
        pyramids = self._pyramid_levels.value()

        if format_name == "JPEG":
            info = f"JPEG quality {quality}%, {pyramids} pyramid levels"
        elif format_name in ("OME-TIFF", "TIFF"):
            comp_names = {0: "none", 1: "fast", 5: "balanced", 9: "maximum"}
            comp_name = comp_names.get(compression, f"level {compression}")
            info = f"Compression: {comp_name}, {pyramids} pyramid levels"
        else:  # PNG
            comp_names = {0: "none", 1: "fast", 5: "balanced", 9: "maximum"}
            comp_name = comp_names.get(compression, f"level {compression}")
            info = f"Lossless compression: {comp_name}, {pyramids} pyramid levels"

        self._info_label.setText(f"ℹ️ {info}")

    def get_options(self) -> dict:
        """Get the selected save options.

        Returns
        -------
        dict
            Dictionary with save option keys and values
        """
        return {
            "pyramid_levels": self._pyramid_levels.value(),
            "compression": self._compression.value(),
            "quality": self._quality.value(),
            "tile_size": int(self._tile_size.currentText()),
            "format": self._format.currentText(),
        }
