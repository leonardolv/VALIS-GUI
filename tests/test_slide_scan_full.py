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
