"""BlinkViewerDialog: Side-by-side must stay fully opaque; sensible defaults."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog


def _make(qtbot, n=2):
    viewer = MagicMock()
    layers = []

    def _open(*_a, **_k):
        layer = MagicMock()
        layer.opacity = 1.0
        layer.visible = True
        layers.append(layer)
        return [layer]

    viewer.open.side_effect = _open
    d = BlinkViewerDialog(viewer, [Path(f"s{i}.tif") for i in range(n)])
    qtbot.addWidget(d)
    return d


def test_slide_b_defaults_to_a_different_slide(qtbot):
    d = _make(qtbot)
    assert d._slide_a.currentIndex() == 0
    assert d._slide_b.currentIndex() == 1


def test_single_slide_does_not_crash(qtbot):
    d = _make(qtbot, n=1)
    assert d._slide_b.currentIndex() == 0


def test_blend_slider_does_not_dim_side_by_side(qtbot):
    d = _make(qtbot)
    d._mode.setCurrentText("Side-by-side")
    assert not d._opacity.isEnabled()
    d._opacity.setValue(10)
    assert d._layer_a.opacity == 1.0
    assert d._layer_b.opacity == 1.0


def test_blend_slider_restored_for_swipe(qtbot):
    d = _make(qtbot)
    d._mode.setCurrentText("Side-by-side")
    d._mode.setCurrentText("Swipe")
    assert d._opacity.isEnabled()
    d._opacity.setValue(25)
    assert d._layer_a.opacity == 0.75
    assert d._layer_b.opacity == 0.25


def test_tooltips_name_real_modes(qtbot):
    d = _make(qtbot)
    tip = d._mode.toolTip()
    for i in range(d._mode.count()):
        assert d._mode.itemText(i) in tip
    assert "Blend:" not in tip
    assert d._slide_a.accessibleName() and d._slide_b.accessibleName()
