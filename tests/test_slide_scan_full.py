"""Tests for the slide scanning service."""

from __future__ import annotations

from pathlib import Path

import pytest

from valis_workstation.services.slide_scan import (
    DEFAULT_EXTENSIONS,
    scan_slide_folder,
)


class TestScanSlideFolder:
    def test_empty_folder(self, tmp_path: Path) -> None:
        result = scan_slide_folder(tmp_path)
        assert result == []

    def test_nonexistent_folder(self, tmp_path: Path) -> None:
        result = scan_slide_folder(tmp_path / "missing")
        assert result == []

    def test_filters_by_extension(self, tmp_path: Path) -> None:
        (tmp_path / "slide.tif").write_text("a")
        (tmp_path / "slide.svs").write_text("b")
        (tmp_path / "notes.txt").write_text("c")
        (tmp_path / "report.pdf").write_text("d")

        slides = scan_slide_folder(tmp_path)
        names = {s.name for s in slides}
        assert "slide.tif" in names
        assert "slide.svs" in names
        assert "notes.txt" not in names
        assert "report.pdf" not in names

    def test_sorted_by_name(self, tmp_path: Path) -> None:
        (tmp_path / "z_slide.tif").write_text("a")
        (tmp_path / "a_slide.tif").write_text("b")
        (tmp_path / "m_slide.tif").write_text("c")

        slides = scan_slide_folder(tmp_path)
        assert [s.name for s in slides] == ["a_slide.tif", "m_slide.tif", "z_slide.tif"]

    def test_case_insensitive_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "slide.TIF").write_text("a")
        (tmp_path / "slide2.Tiff").write_text("b")

        slides = scan_slide_folder(tmp_path)
        assert len(slides) == 2

    def test_custom_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "file.xyz").write_text("a")
        (tmp_path / "file.abc").write_text("b")

        slides = scan_slide_folder(tmp_path, extensions={".xyz"})
        assert len(slides) == 1
        assert slides[0].name == "file.xyz"

    def test_ignores_subdirectories(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "slide.tif").write_text("a")
        (tmp_path / "top.tif").write_text("b")

        slides = scan_slide_folder(tmp_path)
        assert len(slides) == 1
        assert slides[0].name == "top.tif"

    def test_not_a_directory(self, tmp_path: Path) -> None:
        file = tmp_path / "file.txt"
        file.write_text("data")

        result = scan_slide_folder(file)
        assert result == []

    def test_default_extensions_coverage(self) -> None:
        assert ".tif" in DEFAULT_EXTENSIONS
        assert ".tiff" in DEFAULT_EXTENSIONS
        assert ".svs" in DEFAULT_EXTENSIONS
        assert ".ndpi" in DEFAULT_EXTENSIONS
        assert ".png" in DEFAULT_EXTENSIONS
        assert ".jpg" in DEFAULT_EXTENSIONS
        assert ".jpeg" in DEFAULT_EXTENSIONS


class TestSlideDisplayNames:
    def test_unique_stems_use_the_stem(self) -> None:
        from valis_workstation.services.slide_scan import slide_display_names

        a, b = Path("/x/a.ome.tiff"), Path("/x/b.svs")
        assert slide_display_names([a, b]) == {a: "a.ome", b: "b"}

    def test_shared_stems_use_full_file_names(self) -> None:
        from valis_workstation.services.slide_scan import slide_display_names

        a, b, c = Path("/x/HE.tif"), Path("/x/he.svs"), Path("/x/other.tif")
        names = slide_display_names([a, b, c])
        assert names == {a: "HE.tif", b: "he.svs", c: "other"}
        assert len(set(names.values())) == 3


class TestPreviewKeepsSlidesWithSharedStems:
    def test_both_slides_reach_the_preview_and_reference_list(
        self, qtbot, tmp_path
    ) -> None:
        from unittest.mock import patch

        from valis_workstation.main_window import MainWindow
        from valis_workstation.utils.qt_logging import QtLogEmitter

        win = MainWindow(
            repo_root=tmp_path,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(win)
        slides = [tmp_path / "HE.tif", tmp_path / "HE.svs", tmp_path / "z.tif"]
        for s in slides:
            s.write_bytes(b"x")
        with patch(
            "valis_workstation.services.thumbnail_generator.generate_thumbnail",
            return_value=(None, {}),
        ):
            win._load_thumbnails_parallel(slides, overlay=None)
        assert set(win._slide_preview_dock._thumbnails) == {"HE.tif", "HE.svs", "z"}


def test_preview_sort_ignores_case(qtbot) -> None:
    from valis_workstation.ui.slide_preview_dock import SlidePreviewDock

    dock = SlidePreviewDock()
    qtbot.addWidget(dock)
    for n in ["B", "a", "c"]:
        dock.add_slide(n, None, {})
    items = {dock._grid_layout.itemAt(i).widget().property("slideName") for i in range(3)}
    order = [
        dock._grid_layout.itemAtPosition(r, c).widget().property("slideName")
        for r in range(3)
        for c in range(3)
        if dock._grid_layout.itemAtPosition(r, c)
    ]
    assert items == {"B", "a", "c"}
    assert order == ["a", "B", "c"]


class TestFindReferenceSlide:
    def test_exact_case_beats_case_insensitive(self) -> None:
        from valis_workstation.services.slide_scan import find_reference_slide

        paths = ["/d/A.tif", "/d/a.tif"]
        assert find_reference_slide(paths, "a.tif") == "/d/a.tif"
        assert find_reference_slide(paths, "A.tif") == "/d/A.tif"

    def test_stem_name_and_missing(self) -> None:
        from valis_workstation.services.slide_scan import find_reference_slide

        paths = ["/d/HE.tif", "/d/IHC.svs"]
        assert find_reference_slide(paths, "ihc") == "/d/IHC.svs"
        assert find_reference_slide(paths, "HE.tif") == "/d/HE.tif"
        assert find_reference_slide(paths, "nope") is None
