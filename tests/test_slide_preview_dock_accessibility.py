"""Unit tests for SlidePreviewDock accessibility metadata, object names, public properties, ergonomics helpers, and action triggers."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtCore, QtGui

from valis_workstation.ui.slide_preview_dock import SlidePreviewDock


@pytest.fixture
def dock(qtbot):
    d = SlidePreviewDock()
    qtbot.addWidget(d)
    return d


def create_test_pixmap(color: QtGui.QColor, width: int = 100, height: int = 100) -> QtGui.QPixmap:
    pix = QtGui.QPixmap(width, height)
    pix.fill(color)
    return pix


class TestSlidePreviewDockAccessibilityAndErgonomics:
    def test_slide_preview_dock_metadata_and_object_names(self, dock) -> None:
        # 1. Dock accessibility metadata
        assert dock.objectName() == "SlidePreviewDock"
        assert dock.accessibleName() == "Slide Preview Dock"
        assert "thumbnails and metadata cards" in dock.accessibleDescription()

        # 2. Public properties, object names, and pointer cursor affordances
        assert dock.header_label.objectName() == "slidePreviewHeader"
        assert dock.header_label.accessibleName() == "Slide Preview Header"

        assert dock.filter_edit.objectName() == "slideFilterEdit"
        assert dock.filter_edit.accessibleName() == "Filter Slide Thumbnails"
        assert len(dock.filter_edit.accessibleDescription()) > 0

        assert dock.sort_combobox.objectName() == "slideSortCombo"
        assert dock.sort_combobox.accessibleName() == "Sort Slide Thumbnails"
        assert dock.sort_combobox.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dock.sort_combobox.accessibleDescription()) > 0

        assert dock.size_slider.objectName() == "slideSizeSlider"
        assert dock.size_slider.accessibleName() == "Thumbnail Size Slider"
        assert dock.size_slider.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dock.size_slider.accessibleDescription()) > 0

        assert dock.summary_label.objectName() == "slideSummaryLabel"
        assert dock.summary_label.accessibleName() == "Slide Count Summary"

        assert dock.grid_view_button.objectName() == "slideGridViewBtn"
        assert dock.grid_view_button.accessibleName() == "Grid view"
        assert dock.grid_view_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dock.grid_view_button.accessibleDescription()) > 0

        assert dock.list_view_button.objectName() == "slideListViewBtn"
        assert dock.list_view_button.accessibleName() == "List view"
        assert dock.list_view_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
        assert len(dock.list_view_button.accessibleDescription()) > 0

        assert dock.scroll_area.objectName() == "slideScrollArea"
        assert dock.scroll_area.accessibleName() == "Slide Thumbnails Scroll Area"

        assert dock.grid_container.objectName() == "slideGridContainer"

    def test_empty_state_queries(self, dock) -> None:
        assert dock.slide_count() == 0
        assert dock.has_slides() is False
        assert dock.slide_names() == []
        assert dock.visible_slide_count() == 0
        assert dock.visible_slide_names() == []
        assert dock.selected_slide_name() is None
        assert dock.summary_text() == "0 slides"
        assert dock.filter_text() == ""
        assert dock.sort_mode() == "Name (A-Z)"
        assert dock.thumbnail_size() == 128
        assert dock.is_grid_view() is True
        assert dock.is_list_view() is False

    def test_slide_addition_metadata_and_inspection(self, dock) -> None:
        pix1 = create_test_pixmap(QtGui.QColor("red"), 200, 200)
        pix2 = create_test_pixmap(QtGui.QColor("blue"), 150, 150)
        meta1 = {"dimensions": (2000, 2000), "channels": 3, "dtype": "uint8", "file_path": "/slides/sample_a.svs"}

        dock.add_slide("Slide_A", pix1, meta1)
        dock.add_slide("Slide_B", pix2)

        assert dock.slide_count() == 2
        assert dock.has_slides() is True
        assert dock.slide_names() == ["Slide_A", "Slide_B"]
        assert dock.visible_slide_count() == 2
        assert dock.summary_text() == "2 slides"

        # Check slide card widget properties & accessibility
        widget_a = dock.slide_widget("Slide_A")
        assert widget_a is not None
        assert widget_a.objectName() == "SlideCard"
        assert widget_a.accessibleName() == "Slide Card: Slide_A"
        assert "Thumbnail card for slide" in widget_a.accessibleDescription()
        assert widget_a.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        # Check metadata query
        assert dock.slide_metadata("Slide_A") == meta1
        assert dock.slide_metadata("Slide_B") == {}
        assert dock.slide_metadata("Nonexistent") is None

        # Check pixmap query
        assert dock.slide_pixmap("Slide_A") is not None
        assert dock.slide_pixmap("Nonexistent") is None

    def test_slide_selection_and_signals(self, dock) -> None:
        pix = create_test_pixmap(QtGui.QColor("green"))
        dock.add_slide("Slide_1", pix)
        dock.add_slide("Slide_2", pix)

        emitted_signals: list[str] = []
        dock.slide_selected.connect(emitted_signals.append)

        # Select Slide_1
        assert dock.select_slide("Slide_1") is True
        assert dock.selected_slide_name() == "Slide_1"
        assert dock.is_slide_selected("Slide_1") is True
        assert dock.is_slide_selected("Slide_2") is False
        assert emitted_signals == ["Slide_1"]

        # Select Slide_2
        assert dock.select_slide("Slide_2") is True
        assert dock.selected_slide_name() == "Slide_2"
        assert dock.is_slide_selected("Slide_2") is True
        assert emitted_signals == ["Slide_1", "Slide_2"]

        # Select invalid slide
        assert dock.select_slide("Invalid_Slide") is False
        assert dock.selected_slide_name() == "Slide_2"

        # Deselect
        assert dock.select_slide(None) is True
        assert dock.selected_slide_name() is None

    def test_filtering_and_sorting_ergonomics(self, dock) -> None:
        pix = create_test_pixmap(QtGui.QColor("cyan"))
        dock.add_slide("Alpha_Slide", pix)
        dock.add_slide("Beta_Slide", pix)
        dock.add_slide("Gamma_Slide", pix)

        assert dock.visible_slide_names() == ["Alpha_Slide", "Beta_Slide", "Gamma_Slide"]

        # Filter by "beta"
        dock.set_filter_text("beta")
        assert dock.filter_text() == "beta"
        assert dock.visible_slide_count() == 1
        assert dock.visible_slide_names() == ["Beta_Slide"]
        assert dock.summary_text() == "1/3 visible"

        # Clear filter
        dock.clear_filter()
        assert dock.filter_text() == ""
        assert dock.visible_slide_count() == 3
        assert dock.summary_text() == "3 slides"

        # Change sort mode to Z-A
        assert dock.set_sort_mode("Name (Z-A)") is True
        assert dock.sort_mode() == "Name (Z-A)"
        assert dock.visible_slide_names() == ["Gamma_Slide", "Beta_Slide", "Alpha_Slide"]

        # Invalid sort mode
        assert dock.set_sort_mode("Invalid Sort Mode") is False

        # Reset sort mode to A-Z
        assert dock.set_sort_mode("Name (A-Z)") is True
        assert dock.visible_slide_names() == ["Alpha_Slide", "Beta_Slide", "Gamma_Slide"]

    def test_view_mode_and_thumbnail_sizing(self, dock) -> None:
        # Resize thumbnails
        dock.set_thumbnail_size(160)
        assert dock.thumbnail_size() == 160

        # View mode toggles
        assert dock.is_grid_view() is True
        assert dock.is_list_view() is False

        assert dock.set_view_mode("list") is True
        assert dock.is_list_view() is True
        assert dock.is_grid_view() is False

        assert dock.set_view_mode("grid") is True
        assert dock.is_grid_view() is True
        assert dock.is_list_view() is False

        # Invalid view mode
        assert dock.set_view_mode("invalid") is False

        # Programmatic triggers
        dock.trigger_list_view()
        assert dock.is_list_view() is True

        dock.trigger_grid_view()
        assert dock.is_grid_view() is True

    def test_navigation_action_triggers_and_clear(self, dock) -> None:
        pix = create_test_pixmap(QtGui.QColor("yellow"))
        dock.add_slide("Slide_A", pix)
        dock.add_slide("Slide_B", pix)
        dock.add_slide("Slide_C", pix)

        # Initially no selection: select_next picks first
        assert dock.trigger_select_next() is True
        assert dock.selected_slide_name() == "Slide_A"

        # Advance to B
        assert dock.trigger_select_next() is True
        assert dock.selected_slide_name() == "Slide_B"

        # Advance to C
        assert dock.trigger_select_next() is True
        assert dock.selected_slide_name() == "Slide_C"

        # Advance wraps to A
        assert dock.trigger_select_next() is True
        assert dock.selected_slide_name() == "Slide_A"

        # Previous wraps back to C
        assert dock.trigger_select_previous() is True
        assert dock.selected_slide_name() == "Slide_C"

        # Previous back to B
        assert dock.trigger_select_previous() is True
        assert dock.selected_slide_name() == "Slide_B"

        # Programmatic clear trigger
        dock.trigger_clear()
        assert dock.slide_count() == 0
        assert dock.has_slides() is False
        assert dock.selected_slide_name() is None
        assert dock.trigger_select_next() is False
        assert dock.trigger_select_previous() is False
