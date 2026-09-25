"""Dialog for configuring save/export options."""

from __future__ import annotations

from PySide6 import QtWidgets

from valis_workstation.constants import ImageFormats


class SaveOptionsDialog(QtWidgets.QDialog):
    """Dialog for configuring image save options.

    Allows users to customize pyramid levels, compression, quality, and tile size
    for saved registered images, with pre-configured export presets and reset-to-defaults.
    """

    PRESETS: dict[str, dict] = {
        "Default (Balanced OME-TIFF)": {
            "format": ImageFormats.OME_TIFF,
            "pyramid_levels": 4,
            "compression": 1,
            "quality": 95,
            "tile_size": "512",
            "write_pyramid": True,
        },
        "Diagnostic High-Quality": {
            "format": ImageFormats.OME_TIFF,
            "pyramid_levels": 6,
            "compression": 5,
            "quality": 98,
            "tile_size": "512",
            "write_pyramid": True,
        },
        "Web / Fast Preview": {
            "format": ImageFormats.JPEG,
            "pyramid_levels": 3,
            "compression": 1,
            "quality": 85,
            "tile_size": "256",
            "write_pyramid": True,
        },
        "Archival Lossless": {
            "format": ImageFormats.TIFF,
            "pyramid_levels": 5,
            "compression": 9,
            "quality": 100,
            "tile_size": "1024",
            "write_pyramid": True,
        },
    }

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        initial_options: dict | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.setModal(True)
        self.setMinimumWidth(440)
        self._is_updating_preset = False

        layout = QtWidgets.QVBoxLayout(self)

        # Form layout for options
        form = QtWidgets.QFormLayout()

        # Batch Export Preset Selector
        self._preset_combo = QtWidgets.QComboBox()
        self._preset_combo.setObjectName("export_preset_combo")
        self._preset_combo.setAccessibleName("Export Preset Selection")
        self._preset_combo.addItems(list(self.PRESETS.keys()) + ["Custom"])
        self._preset_combo.setToolTip("Quickly select optimized settings for standard export scenarios")
        form.addRow("Preset:", self._preset_combo)

        # Write pyramid checkbox (C4)
        self._write_pyramid = QtWidgets.QCheckBox("Write image pyramid")
        self._write_pyramid.setObjectName("write_pyramid_check")
        self._write_pyramid.setAccessibleName("Write Image Pyramid Checkbox")
        self._write_pyramid.setChecked(True)
        self._write_pyramid.setToolTip("Enable multi-resolution pyramid output for faster viewer performance")
        form.addRow("", self._write_pyramid)

        # Pyramid levels
        self._pyramid_levels = QtWidgets.QSpinBox()
        self._pyramid_levels.setObjectName("pyramid_levels_spin")
        self._pyramid_levels.setAccessibleName("Pyramid Levels")
        self._pyramid_levels.setRange(0, 10)
        self._pyramid_levels.setValue(4)
        self._pyramid_levels.setToolTip(
            "Number of pyramid levels for multi-resolution images.\n"
            "More levels = better viewer performance but larger file size.\n"
            "Recommended: 4-6 for whole slide images."
        )
        form.addRow("Pyramid levels:", self._pyramid_levels)
        self._write_pyramid.toggled.connect(self._pyramid_levels.setEnabled)

        # Compression level
        self._compression = QtWidgets.QSpinBox()
        self._compression.setObjectName("compression_spin")
        self._compression.setAccessibleName("Compression Level")
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
        self._quality.setObjectName("quality_spin")
        self._quality.setAccessibleName("Image Quality Percentage")
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
        self._tile_size.setObjectName("tile_size_combo")
        self._tile_size.setAccessibleName("Tile Size Pixels")
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
        self._format.setObjectName("format_combo")
        self._format.setAccessibleName("Output Image Format")
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
        self._info_label.setObjectName("save_options_info_label")
        self._info_label.setAccessibleName("Export Info Summary")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #888; font-style: italic;")
        self._update_info()
        layout.addWidget(self._info_label)

        # Connect signals to update info and custom preset state
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        self._pyramid_levels.valueChanged.connect(self._on_control_modified)
        self._compression.valueChanged.connect(self._on_control_modified)
        self._quality.valueChanged.connect(self._on_control_modified)
        self._tile_size.currentTextChanged.connect(self._on_control_modified)
        self._format.currentTextChanged.connect(self._on_control_modified)
        self._write_pyramid.toggled.connect(self._on_control_modified)

        # Dialog buttons with Reset to Defaults
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Reset
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        reset_btn = self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Reset)
        if reset_btn is not None:
            reset_btn.setText("Reset to Defaults")
            reset_btn.setObjectName("reset_defaults_btn")
            reset_btn.setAccessibleName("Reset Export Options to Defaults")
            reset_btn.setToolTip("Reset all save options to recommended workstation defaults")
            reset_btn.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.buttons)

        # Apply initial options if provided
        if initial_options:
            self.apply_options(initial_options)

    def _on_preset_changed(self, preset_name: str) -> None:
        if self._is_updating_preset or preset_name == "Custom":
            return
        if preset_name in self.PRESETS:
            preset = self.PRESETS[preset_name]
            self._is_updating_preset = True
            try:
                self._format.setCurrentText(str(preset["format"]))
                self._pyramid_levels.setValue(int(preset["pyramid_levels"]))
                self._compression.setValue(int(preset["compression"]))
                self._quality.setValue(int(preset["quality"]))
                self._tile_size.setCurrentText(str(preset["tile_size"]))
                self._write_pyramid.setChecked(bool(preset["write_pyramid"]))
            finally:
                self._is_updating_preset = False
            self._update_info()

    def _on_control_modified(self, *_) -> None:
        if not self._is_updating_preset:
            # Check if current control settings match any preset; if not, set to Custom
            matched_preset = "Custom"
            current_vals = {
                "format": self._format.currentText(),
                "pyramid_levels": self._pyramid_levels.value(),
                "compression": self._compression.value(),
                "quality": self._quality.value(),
                "tile_size": self._tile_size.currentText(),
                "write_pyramid": self._write_pyramid.isChecked(),
            }
            for name, p in self.PRESETS.items():
                if all(current_vals[k] == p[k] for k in p):
                    matched_preset = name
                    break
            self._is_updating_preset = True
            self._preset_combo.setCurrentText(matched_preset)
            self._is_updating_preset = False
        self._update_info()

    def reset_to_defaults(self) -> None:
        """Reset all options to standard defaults."""
        self._preset_combo.setCurrentText("Default (Balanced OME-TIFF)")

    def apply_options(self, options: dict) -> None:
        """Apply a dictionary of save options to the dialog controls."""
        self._is_updating_preset = True
        try:
            if "format" in options and options["format"] in ImageFormats.all():
                self._format.setCurrentText(str(options["format"]))
            if "pyramid_levels" in options:
                self._pyramid_levels.setValue(int(options["pyramid_levels"]))
            if "compression" in options:
                self._compression.setValue(int(options["compression"]))
            if "quality" in options:
                self._quality.setValue(int(options["quality"]))
            if "tile_size" in options:
                self._tile_size.setCurrentText(str(options["tile_size"]))
            if "write_pyramid" in options:
                self._write_pyramid.setChecked(bool(options["write_pyramid"]))
        finally:
            self._is_updating_preset = False
        self._on_control_modified()

    def _update_info(self) -> None:
        """Update the info label with current settings summary."""
        format_name = self._format.currentText()
        compression = self._compression.value()
        quality = self._quality.value()
        pyramids = self._pyramid_levels.value()
        write_pyr = self._write_pyramid.isChecked()
        pyr_str = f"{pyramids} pyramid levels" if write_pyr else "single-resolution"

        if format_name == "JPEG":
            info = f"JPEG quality {quality}%, {pyr_str}"
        elif format_name in ("OME-TIFF", "TIFF"):
            comp_names = {0: "none", 1: "fast", 5: "balanced", 9: "maximum"}
            comp_name = comp_names.get(compression, f"level {compression}")
            info = f"Compression: {comp_name}, {pyr_str}"
        else:  # PNG
            comp_names = {0: "none", 1: "fast", 5: "balanced", 9: "maximum"}
            comp_name = comp_names.get(compression, f"level {compression}")
            info = f"Lossless compression: {comp_name}, {pyr_str}"

        self._info_label.setText(f"Info: {info}")

    def get_options(self) -> dict:
        """Get the selected save options.

        Returns
        -------
        dict
            Dictionary with save option keys and values
        """
        return {
            "write_pyramid": self._write_pyramid.isChecked(),
            "pyramid_levels": self._pyramid_levels.value(),
            "compression": self._compression.value(),
            "quality": self._quality.value(),
            "tile_size": int(self._tile_size.currentText()),
            "format": self._format.currentText(),
            "preset": self._preset_combo.currentText(),
        }
