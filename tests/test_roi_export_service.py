"""ROI export service and JSON paste validation (headless)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from valis_workstation.services.roi_export import clamp_bbox, export_roi_crops


class _Img:
    def __init__(self, w, h):
        self.width, self.height = w, h
        self.calls = []

    def extract_area(self, x, y, w, h):
        self.calls.append((x, y, w, h))
        return ("crop", x, y, w, h)


def _slide(w, h):
    img = _Img(w, h)
    return SimpleNamespace(warp_slide=lambda level=0: img), img


def test_clamp_bbox():
    assert clamp_bbox((10, 10, 50, 50), 100, 100) == (10, 10, 50, 50)
    assert clamp_bbox((80, 90, 50, 50), 100, 100) == (80, 90, 20, 10)
    assert clamp_bbox((100, 0, 10, 10), 100, 100) is None
    assert clamp_bbox((0, 200, 10, 10), 100, 100) is None


def test_bad_slide_does_not_abort_batch_and_is_reported(tmp_path):
    ok, ok_img = _slide(1000, 1000)
    small, _ = _slide(50, 50)
    clipped, clip_img = _slide(120, 1000)
    slides = {"a": ok, "small": small, "c": clipped}
    saved = []
    res = export_roi_crops(
        slides, (100, 100, 100, 100), tmp_path, ".png",
        lambda path, img: saved.append(path),
    )
    assert [Path(f).name for f in res.files] == ["a_ROI.png", "c_ROI.png"]
    assert "small" in res.failed and "outside" in res.failed["small"]
    assert res.clipped == ["c"]
    assert clip_img.calls == [(100, 100, 20, 100)]
    assert "failed" in res.summary() and "clipped" in res.summary()


def test_save_failure_is_per_slide(tmp_path):
    a, _ = _slide(500, 500)
    b, _ = _slide(500, 500)

    def save(path, img):
        if "a_ROI" in path:
            raise OSError("disk full")

    res = export_roi_crops({"a": a, "b": b}, (0, 0, 10, 10), tmp_path, ".tiff", save)
    assert res.failed == {"a": "disk full"}
    assert len(res.files) == 1


def test_cancel_stops_and_flags(tmp_path):
    a, _ = _slide(500, 500)
    b, _ = _slide(500, 500)
    calls = {"n": 0}

    def cancelled():
        calls["n"] += 1
        return calls["n"] > 1

    res = export_roi_crops(
        {"a": a, "b": b}, (0, 0, 10, 10), tmp_path, ".tiff",
        lambda p, i: None, is_cancelled=cancelled,
    )
    assert res.cancelled and len(res.files) == 1
    assert "cancelled" in res.summary()


@pytest.mark.parametrize(
    "payload",
    [
        {"x": 5, "y": 6, "width": 20, "height": "bad"},
        {"x": 5, "width": 10**30},
        {"x": True},
        {"x": 5, "y": -3},
        {"x": float("nan")},
    ],
)
def test_paste_is_atomic_on_invalid_values(qtbot, payload):
    pytest.importorskip("PySide6")
    from PySide6 import QtWidgets
    from valis_workstation.ui.dialogs.roi_export_dialog import ROIExportDialog

    d = ROIExportDialog()
    qtbot.addWidget(d)
    QtWidgets.QApplication.clipboard().setText(json.dumps(payload))
    d.paste_json_btn.click()
    assert d.get_options()["bbox"] == (0, 0, 1000, 1000)
    assert "Invalid ROI JSON" in d._feedback_label.text()


def test_case_only_name_clash_does_not_overwrite(tmp_path):
    a, _ = _slide(1000, 1000)
    b, _ = _slide(1000, 1000)
    res = export_roi_crops(
        {"Slide": a, "slide": b}, (0, 0, 10, 10), tmp_path, ".png",
        lambda path, img: None,
    )
    assert [Path(f).name for f in res.files] == ["Slide_ROI.png", "slide_ROI_2.png"]
