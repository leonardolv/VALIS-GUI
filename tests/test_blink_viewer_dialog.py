from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from PySide6 import QtCore, QtWidgets
import pytest

from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog


class _MockLayer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.visible = True
        self.opacity = 1.0


class _MockLayers(list):
    def remove(self, item):
        if item in self:
            super().remove(item)


class _MockViewer:
    def __init__(self) -> None:
        self.layers = _MockLayers()

    def open(self, path: str, name: str = "") -> _MockLayer:
        layer = _MockLayer(name)
        self.layers.append(layer)
        return layer


@pytest.fixture()
def mock_viewer():
    return _MockViewer()


def test_blink_viewer_dialog_accessibility_and_affordances(qtbot, mock_viewer):
    slides = [Path("slide_a.tif"), Path("slide_b.tif")]
    dlg = BlinkViewerDialog(viewer=mock_viewer, slide_paths=slides)
    qtbot.addWidget(dlg)

    # Dialog attributes
    assert dlg.objectName() == "blinkViewerDialog"
    assert dlg.accessibleName() == "Blink Viewer Dialog"

    # Widgets object names and accessibility
    assert dlg._slide_a.objectName() == "blinkSlideACombo"
    assert dlg._slide_a.accessibleName() == "Slide A Selection"
    assert "slide a" in dlg._slide_a.toolTip().lower()
    assert dlg._slide_a.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dlg._slide_b.objectName() == "blinkSlideBCombo"
    assert dlg._slide_b.accessibleName() == "Slide B Selection"
    assert "slide b" in dlg._slide_b.toolTip().lower()
    assert dlg._slide_b.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dlg._mode.objectName() == "blinkModeCombo"
    assert dlg._mode.accessibleName() == "Display Mode Selection"
    assert dlg._mode.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dlg._interval_spin.objectName() == "blinkIntervalSpin"
    assert dlg._interval_spin.accessibleName() == "Blink Interval Milliseconds"
    assert dlg._interval_spin.value() == 600
    assert dlg._interval_spin.suffix() == " ms"

    assert dlg._opacity.objectName() == "blinkOpacitySlider"
    assert dlg._opacity.accessibleName() == "Blend Opacity Slider"
    assert dlg._opacity.value() == 50

    assert dlg._blink_toggle.objectName() == "blinkToggleBtn"
    assert dlg._blink_toggle.accessibleName() == "Toggle Auto Blink"
    assert dlg._blink_toggle.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    assert dlg._button_box.objectName() == "blinkButtonBox"
    assert dlg._button_box.accessibleName() == "Blink Viewer Actions"

    assert dlg._close_btn is not None
    assert dlg._close_btn.objectName() == "blinkCloseBtn"
    assert dlg._close_btn.accessibleName() == "Close Blink Viewer"
    assert dlg._close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_blink_viewer_interval_and_modes(qtbot, mock_viewer):
    slides = [Path("sample1.tif"), Path("sample2.tif")]
    dlg = BlinkViewerDialog(viewer=mock_viewer, slide_paths=slides)
    qtbot.addWidget(dlg)

    # Change interval
    dlg._interval_spin.setValue(850)
    assert dlg._timer.interval() == 850

    # Start blink
    dlg._blink_toggle.setChecked(True)
    assert dlg._timer.isActive()
    assert dlg._blink_toggle.text() == "Stop Blink"

    # Switch mode to Side-by-side: timer stops, blink toggle and interval spin are disabled
    dlg._mode.setCurrentText("Side-by-side")
    assert not dlg._timer.isActive()
    assert not dlg._blink_toggle.isChecked()
    assert not dlg._blink_toggle.isEnabled()
    assert not dlg._interval_spin.isEnabled()

    # Switch back to Blink mode
    dlg._mode.setCurrentText("Blink")
    assert dlg._blink_toggle.isEnabled()
    assert dlg._interval_spin.isEnabled()


def test_blink_viewer_dismissal_stops_timer(qtbot, mock_viewer):
    slides = [Path("sample1.tif"), Path("sample2.tif")]
    dlg = BlinkViewerDialog(viewer=mock_viewer, slide_paths=slides)
    qtbot.addWidget(dlg)

    dlg._blink_toggle.setChecked(True)
    assert dlg._timer.isActive()
    dlg.reject()
    assert not dlg._timer.isActive()

    dlg._blink_toggle.setChecked(True)
    assert dlg._timer.isActive()
    dlg.close()
    assert not dlg._timer.isActive()


def test_blink_viewer_empty_slides(qtbot):
    dlg = BlinkViewerDialog(viewer=None, slide_paths=[])
    qtbot.addWidget(dlg)
    assert dlg._slide_a.count() == 0
    assert dlg._slide_b.count() == 0
    assert dlg._layer_a is None
    assert dlg._layer_b is None
