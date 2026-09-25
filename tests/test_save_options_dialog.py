"""Tests for SaveOptionsDialog presets, accessibility, reset defaults, and option mapping."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from valis_workstation.constants import ImageFormats
from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog


class TestSaveOptionsDialogFeatures:
    def test_default_initialization_and_accessibility(self, qtbot) -> None:
        dlg = SaveOptionsDialog()
        qtbot.addWidget(dlg)

        assert dlg._preset_combo.accessibleName() == "Export Preset Selection"
        assert dlg._write_pyramid.accessibleName() == "Write Image Pyramid Checkbox"
        assert dlg._pyramid_levels.accessibleName() == "Pyramid Levels"
        assert dlg._compression.accessibleName() == "Compression Level"
        assert dlg._quality.accessibleName() == "Image Quality Percentage"
        assert dlg._tile_size.accessibleName() == "Tile Size Pixels"
        assert dlg._format.accessibleName() == "Output Image Format"
        assert dlg._info_label.accessibleName() == "Export Info Summary"

        reset_btn = dlg.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Reset)
        assert reset_btn is not None
        assert reset_btn.text() == "Reset to Defaults"
        assert reset_btn.accessibleName() == "Reset Export Options to Defaults"

        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.OME_TIFF
        assert opts["pyramid_levels"] == 4
        assert opts["compression"] == 1
        assert opts["quality"] == 95
        assert opts["tile_size"] == 512
        assert opts["write_pyramid"] is True
        assert opts["preset"] == "Default (Balanced OME-TIFF)"

    def test_initial_options_population(self, qtbot) -> None:
        custom_opts = {
            "format": ImageFormats.TIFF,
            "pyramid_levels": 6,
            "compression": 7,
            "quality": 88,
            "tile_size": 1024,
            "write_pyramid": False,
        }
        dlg = SaveOptionsDialog(initial_options=custom_opts)
        qtbot.addWidget(dlg)

        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.TIFF
        assert opts["pyramid_levels"] == 6
        assert opts["compression"] == 7
        assert opts["quality"] == 88
        assert opts["tile_size"] == 1024
        assert opts["write_pyramid"] is False
        assert opts["preset"] == "Custom"
        assert "single-resolution" in dlg._info_label.text()

    def test_preset_selection_updates_controls(self, qtbot) -> None:
        dlg = SaveOptionsDialog()
        qtbot.addWidget(dlg)

        # Switch to Diagnostic High-Quality
        dlg._preset_combo.setCurrentText("Diagnostic High-Quality")
        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.OME_TIFF
        assert opts["pyramid_levels"] == 6
        assert opts["compression"] == 5
        assert opts["quality"] == 98
        assert opts["tile_size"] == 512

        # Switch to Web / Fast Preview
        dlg._preset_combo.setCurrentText("Web / Fast Preview")
        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.JPEG
        assert opts["pyramid_levels"] == 3
        assert opts["quality"] == 85
        assert opts["tile_size"] == 256
        assert "JPEG quality 85%" in dlg._info_label.text()

        # Switch to Archival Lossless
        dlg._preset_combo.setCurrentText("Archival Lossless")
        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.TIFF
        assert opts["pyramid_levels"] == 5
        assert opts["compression"] == 9
        assert opts["tile_size"] == 1024

    def test_modifying_control_switches_preset_to_custom(self, qtbot) -> None:
        dlg = SaveOptionsDialog()
        qtbot.addWidget(dlg)

        dlg._preset_combo.setCurrentText("Default (Balanced OME-TIFF)")
        assert dlg._preset_combo.currentText() == "Default (Balanced OME-TIFF)"

        # Tweak compression from 1 to 3
        dlg._compression.setValue(3)
        assert dlg._preset_combo.currentText() == "Custom"

    def test_reset_to_defaults_button(self, qtbot) -> None:
        custom_opts = {
            "format": ImageFormats.JPEG,
            "pyramid_levels": 1,
            "compression": 8,
            "quality": 50,
            "tile_size": 128,
            "write_pyramid": False,
        }
        dlg = SaveOptionsDialog(initial_options=custom_opts)
        qtbot.addWidget(dlg)

        reset_btn = dlg.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Reset)
        assert reset_btn is not None
        reset_btn.click()

        opts = dlg.get_options()
        assert opts["format"] == ImageFormats.OME_TIFF
        assert opts["pyramid_levels"] == 4
        assert opts["compression"] == 1
        assert opts["quality"] == 95
        assert opts["tile_size"] == 512
        assert opts["write_pyramid"] is True
        assert opts["preset"] == "Default (Balanced OME-TIFF)"
