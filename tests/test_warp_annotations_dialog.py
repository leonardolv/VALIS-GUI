"""Tests for WarpAnnotationsDialog accessibility, tooltips, hand cursors, and headless safety."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.warp_annotations import WarpAnnotationsDialog


class MockSlide:
    def __init__(self, name: str) -> None:
        self.name = name

    def warp_geojson_from_to(self, *args, **kwargs):
        return {"type": "FeatureCollection", "features": [{"type": "Feature"}]}


class MockRegistrar:
    def __init__(self, slide_names: list[str]) -> None:
        self.non_rigid_registrar_cls = MagicMock()
        self._slides = {f"/path/{name}.ndpi": MockSlide(name) for name in slide_names}

    def get_sorted_img_f_list(self) -> list[str]:
        return list(self._slides.keys())

    def get_slide(self, path: str):
        return self._slides[path]


def test_warp_annotations_dialog_accessibility_and_tooltips(qtbot, tmp_path):
    registrar = MockRegistrar(["Slide_A", "Slide_B"])
    dialog = WarpAnnotationsDialog(registrar, tmp_path)
    qtbot.addWidget(dialog)

    # LineEdits accessibility and placeholders
    assert dialog._annotation_path.accessibleName() == "Annotation file path"
    assert "geojson" in dialog._annotation_path.toolTip().lower()
    assert "source" in dialog._annotation_path.placeholderText().lower()

    assert dialog._output_dir_edit.accessibleName() == "Warped annotations output directory"
    assert "warped" in dialog._output_dir_edit.toolTip().lower()

    # Source slide combo accessibility and cursor
    assert dialog._source_slide.accessibleName() == "Source slide selection"
    assert dialog._source_slide.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._source_slide.count() == 2

    # Browse buttons accessibility, tooltips, and cursors
    assert dialog._browse_annotation_btn.accessibleName() == "Browse annotation file"
    assert dialog._browse_annotation_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "browse" in dialog._browse_annotation_btn.toolTip().lower()

    assert dialog._browse_output_btn.accessibleName() == "Browse output directory"
    assert dialog._browse_output_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "browse" in dialog._browse_output_btn.toolTip().lower()

    # Status label
    assert dialog._status.accessibleName() == "Warp status message"

    # Action buttons accessibility, tooltips, and cursors
    assert dialog._ok_btn is not None
    assert dialog._ok_btn.accessibleName() == "Warp annotations"
    assert dialog._ok_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "transform" in dialog._ok_btn.toolTip().lower()

    assert dialog._cancel_btn is not None
    assert dialog._cancel_btn.accessibleName() == "Cancel"
    assert dialog._cancel_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert "close" in dialog._cancel_btn.toolTip().lower()


def test_warp_annotations_dialog_browse_callbacks(qtbot, tmp_path, monkeypatch):
    registrar = MockRegistrar(["Slide_A", "Slide_B"])
    dialog = WarpAnnotationsDialog(registrar, tmp_path)
    qtbot.addWidget(dialog)

    test_file = str(tmp_path / "regions.geojson")
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (test_file, "GeoJSON (*.geojson)"),
    )
    dialog._browse_annotation_btn.click()
    assert dialog._annotation_path.text() == test_file

    test_out = str(tmp_path / "custom_output")
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: test_out,
    )
    dialog._browse_output_btn.click()
    assert dialog._output_dir_edit.text() == test_out


def test_warp_annotations_dialog_validation_headless_safety(qtbot, tmp_path):
    registrar = MockRegistrar(["Slide_A", "Slide_B"])
    dialog = WarpAnnotationsDialog(registrar, tmp_path)
    qtbot.addWidget(dialog)

    # Empty annotation path should not raise or block
    dialog._annotation_path.setText("")
    dialog._ok_btn.click()
    assert dialog._status.text() == "Annotation file not found."

    # Non-existent file
    dialog._annotation_path.setText(str(tmp_path / "nonexistent.geojson"))
    dialog._ok_btn.click()
    assert dialog._status.text() == "Annotation file not found."


def test_warp_annotations_dialog_run_warp_success(qtbot, tmp_path):
    registrar = MockRegistrar(["Slide_A", "Slide_B"])
    dialog = WarpAnnotationsDialog(registrar, tmp_path)
    qtbot.addWidget(dialog)

    # Create dummy source geojson
    sample_geojson = tmp_path / "sample.geojson"
    sample_geojson.write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    dialog._annotation_path.setText(str(sample_geojson))

    out_folder = tmp_path / "output_test"
    dialog._output_dir_edit.setText(str(out_folder))

    dialog._run_warp()

    assert "saved" in dialog._status.text().lower()
    assert (out_folder / "Slide_A_to_Slide_A.geojson").exists()
    assert (out_folder / "Slide_A_to_Slide_B.geojson").exists()
