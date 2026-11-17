"""Tests for LayerControlsDock accessibility metadata, object names, public properties, and ergonomics helpers."""

from __future__ import annotations

import types
import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
from valis_workstation.ui.layer_controls_dock import LayerControlsDock, COLORMAP_OPTIONS


class MockColormap:
    def __init__(self, name: str) -> None:
        self.name = name


class MockLayer:
    def __init__(self, name: str, visible: bool = True, opacity: float = 1.0, colormap_name: str | None = None) -> None:
        self.name = name
        self.visible = visible
        self.opacity = opacity
        self.colormap = MockColormap(colormap_name) if colormap_name else None


class MockViewer:
    def __init__(self, layers: list | None = None) -> None:
        self.layers = layers if layers is not None else []


class TestLayerControlsDockAccessibilityAndErgonomics:
    def test_layer_controls_dock_metadata_and_empty_state(self, qtbot) -> None:
        viewer = MockViewer([])
        dock = LayerControlsDock(viewer)
        qtbot.addWidget(dock)

        # 1. Dock accessibility metadata
        assert dock.objectName() == "LayerControlsDock"
        assert dock.accessibleName() == "Layer Controls Dock"
        assert len(dock.accessibleDescription()) > 0

        # 2. Public properties and object names
        assert dock.search_edit.objectName() == "layerSearchEdit"
        assert dock.search_edit.accessibleName() == "Search layer names"

        assert dock.lock_checkbox.objectName() == "layerLockEditsCheck"
        assert dock.lock_checkbox.accessibleName() == "Lock layer edits"
        assert dock.lock_checkbox.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.solo_button.objectName() == "layerSoloBtn"
        assert dock.solo_button.accessibleName() == "Solo selected layer"
        assert dock.solo_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert dock.solo_button.isEnabled() is False

        assert dock.reset_opacity_button.objectName() == "layerResetOpacityBtn"
        assert dock.reset_opacity_button.accessibleName() == "Reset layer opacities"
        assert dock.reset_opacity_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert dock.reset_opacity_button.isEnabled() is False

        assert dock.show_all_button.objectName() == "layerShowAllBtn"
        assert dock.show_all_button.accessibleName() == "Show all layers"
        assert dock.show_all_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert dock.show_all_button.isEnabled() is False

        assert dock.table_widget.objectName() == "layerTableWidget"
        assert dock.table_widget.accessibleName() == "Layers table"

        # 3. Ergonomic state queries on empty dock
        assert dock.layer_count() == 0
        assert dock.visible_layer_count() == 0
        assert dock.has_layers() is False
        assert dock.is_locked() is False
        assert dock.layer_names() == []
        assert dock.layer_row("non_existent") == -1
        assert dock.is_layer_visible(0) is False
        assert dock.layer_opacity(0) == 0.0
        assert dock.layer_colormap(0) is None

        dock.close()

    def test_layer_controls_dock_with_layers_and_ergonomics(self, qtbot) -> None:
        l1 = MockLayer("DAPI", visible=True, opacity=1.0, colormap_name="blue")
        l2 = MockLayer("GFP", visible=True, opacity=0.8, colormap_name="green")
        l3 = MockLayer("RFP", visible=False, opacity=0.5, colormap_name="red")

        viewer = MockViewer([l1, l2, l3])
        dock = LayerControlsDock(viewer)
        qtbot.addWidget(dock)

        # Buttons should now be enabled
        assert dock.solo_button.isEnabled() is True
        assert dock.reset_opacity_button.isEnabled() is True
        assert dock.show_all_button.isEnabled() is True

        # State queries
        assert dock.layer_count() == 3
        assert dock.visible_layer_count() == 2
        assert dock.has_layers() is True
        assert dock.layer_names() == ["DAPI", "GFP", "RFP"]
        assert dock.layer_row("GFP") == 1
        assert dock.layer_row("gfp") == 1

        # Check cell widgets affordances
        for r in range(3):
            cb = dock.table_widget.cellWidget(r, 0)
            assert isinstance(cb, QtWidgets.QCheckBox)
            assert cb.objectName() == f"layerVisibleCheck_{r}"
            assert cb.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
            assert "visibility" in cb.accessibleName().lower()

            slider = dock.table_widget.cellWidget(r, 2)
            assert isinstance(slider, QtWidgets.QSlider)
            assert slider.objectName() == f"layerOpacitySlider_{r}"
            assert slider.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
            assert "opacity" in slider.accessibleName().lower()

            combo = dock.table_widget.cellWidget(r, 3)
            assert isinstance(combo, QtWidgets.QComboBox)
            assert combo.objectName() == f"layerColormapCombo_{r}"
            assert combo.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
            assert "colormap" in combo.accessibleName().lower()

        # Query and mutate visibility
        assert dock.is_layer_visible("DAPI") is True
        assert dock.is_layer_visible("RFP") is False
        assert dock.set_layer_visible("RFP", True) is True
        assert dock.is_layer_visible("RFP") is True
        assert dock.visible_layer_count() == 3

        # Query and mutate opacity
        assert pytest.approx(dock.layer_opacity("GFP"), 0.05) == 0.8
        assert dock.set_layer_opacity("GFP", 0.35) is True
        assert pytest.approx(dock.layer_opacity("GFP"), 0.05) == 0.35

        # Query and mutate colormap
        assert dock.layer_colormap("DAPI") == "blue"
        assert dock.set_layer_colormap("DAPI", "cyan") is True
        assert dock.layer_colormap("DAPI") == "cyan"

        # Search / filter text
        dock.set_filter_text("rfp")
        assert dock.filter_text() == "rfp"
        assert dock.table_widget.isRowHidden(0) is True  # DAPI hidden
        assert dock.table_widget.isRowHidden(1) is True  # GFP hidden
        assert dock.table_widget.isRowHidden(2) is False  # RFP visible

        dock.set_filter_text("")
        assert dock.table_widget.isRowHidden(0) is False
        assert dock.table_widget.isRowHidden(1) is False
        assert dock.table_widget.isRowHidden(2) is False

        # Programmatic triggers
        dock.table_widget.setCurrentCell(1, 1)  # select GFP
        dock.trigger_solo_selected()
        assert dock.is_layer_visible("GFP") is True
        assert dock.is_layer_visible("DAPI") is False
        assert dock.is_layer_visible("RFP") is False

        dock.trigger_show_all()
        assert dock.is_layer_visible("DAPI") is True
        assert dock.is_layer_visible("GFP") is True
        assert dock.is_layer_visible("RFP") is True

        dock.trigger_reset_opacity()
        assert pytest.approx(dock.layer_opacity("GFP"), 0.05) == 1.0
        assert pytest.approx(dock.layer_opacity("DAPI"), 0.05) == 1.0

        # Lock edits
        dock.set_locked(True)
        assert dock.is_locked() is True
        dock.trigger_solo_selected()  # Should not mutate when locked
        assert dock.is_layer_visible("DAPI") is True

        dock.trigger_refresh()
        dock.close()
