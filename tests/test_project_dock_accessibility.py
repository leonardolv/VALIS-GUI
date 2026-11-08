"""Tests for ProjectDock accessibility, object names, public properties, and ergonomics helpers."""

from __future__ import annotations

from pathlib import Path
import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
from valis_workstation.ui.project_dock import ProjectDock


class TestProjectDockAccessibilityAndErgonomics:
    def test_project_dock_accessibility_and_properties(self, qtbot) -> None:
        dock = ProjectDock()
        qtbot.addWidget(dock)

        # Dock metadata
        assert dock.objectName() == "ProjectDock"
        assert dock.accessibleName() == "Project Dock"
        assert dock.accessibleDescription() == "Slide list and project management panel"

        # Child controls object names and accessibility
        assert dock.slides_header.objectName() == "projectSlidesHeader"
        assert dock.slides_header.accessibleName() == "Slides Header"

        assert dock.filter_edit.objectName() == "projectFilterInput"
        assert dock.filter_edit.accessibleName() == "Filter slides by filename"

        assert dock.empty_label.objectName() == "projectEmptyLabel"
        assert dock.empty_label.accessibleName() == "No slides loaded notification"

        assert dock.open_folder_button.objectName() == "projectOpenFolderBtn"
        assert dock.open_folder_button.accessibleName() == "Open slide folder"
        assert (
            dock.open_folder_button.cursor().shape()
            == QtCore.Qt.CursorShape.PointingHandCursor
        )

        assert dock.list_widget.objectName() == "projectListWidget"
        assert dock.list_widget.accessibleName() == "Loaded Slide List"

        assert dock.clear_button.objectName() == "projectClearAllBtn"
        assert dock.clear_button.accessibleName() == "Clear all slides"
        assert (
            dock.clear_button.cursor().shape()
            == QtCore.Qt.CursorShape.PointingHandCursor
        )

        assert dock.remove_selected_button.objectName() == "projectRemoveSelectedBtn"
        assert dock.remove_selected_button.accessibleName() == "Remove selected slides"
        assert (
            dock.remove_selected_button.cursor().shape()
            == QtCore.Qt.CursorShape.PointingHandCursor
        )

        # Public properties references
        assert dock.filter_edit is dock._filter_edit
        assert dock.list_widget is dock._list
        assert dock.clear_button is dock._clear_button
        assert dock.remove_selected_button is dock._remove_selected_button
        assert dock.open_folder_button is dock._open_folder_button
        assert dock.empty_label is dock._empty_label
        assert dock.slides_header is dock._slides_header

    def test_project_dock_queries_selection_and_actions(self, qtbot, tmp_path: Path) -> None:
        dock = ProjectDock()
        qtbot.addWidget(dock)

        # Initial empty state
        assert dock.slide_count() == 0
        assert dock.visible_slide_count() == 0
        assert dock.has_slides() is False
        assert dock.selected_slide_paths() == []
        assert dock.selected_slide_names() == []
        assert dock.filter_text() == ""

        # Open folder trigger signal
        open_folder_emitted = []
        dock.open_folder_requested.connect(lambda: open_folder_emitted.append(True))
        dock.trigger_open_folder()
        assert len(open_folder_emitted) == 1

        # Populate slides
        s1 = tmp_path / "slide1.svs"
        s2 = tmp_path / "slide2.ndpi"
        s3 = tmp_path / "slide3.mrxs"
        s1.write_text("1")
        s2.write_text("2")
        s3.write_text("3")

        dock.set_slides([s1, s2, s3])
        assert dock.slide_count() == 3
        assert dock.visible_slide_count() == 3
        assert dock.has_slides() is True

        # Filter query and mutation
        dock.set_filter_text("ndpi")
        assert dock.filter_text() == "ndpi"
        assert dock.visible_slide_count() == 1

        dock.set_filter_text("")
        assert dock.visible_slide_count() == 3

        # Selection helpers
        assert dock.select_slide("slide2.ndpi") is True
        assert dock.selected_slide_names() == ["slide2.ndpi"]
        assert dock.selected_slide_paths() == [s2]

        assert dock.select_slide(s3) is True
        assert dock.selected_slide_names() == ["slide3.mrxs"]
        assert dock.selected_slide_paths() == [s3]

        assert dock.select_slide("nonexistent_slide.tif") is False

        dock.select_all_slides()
        assert len(dock.selected_slide_names()) == 3
        assert len(dock.selected_slide_paths()) == 3

        dock.clear_selection()
        assert len(dock.selected_slide_names()) == 0

        # Programmatic remove selected trigger
        assert dock.select_slide("slide1.svs") is True
        dock.trigger_remove_selected()
        assert dock.slide_count() == 2
        assert "slide1.svs" not in dock.selected_slide_names()

        # Programmatic clear all trigger (headless safe)
        dock.trigger_clear_all()
        assert dock.slide_count() == 0
        assert dock.has_slides() is False
