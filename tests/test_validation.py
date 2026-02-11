"""Tests for validation utilities."""
from __future__ import annotations

from pathlib import Path

import pytest

from valis_workstation.utils.validation import ValidationResult, validate_slides


class TestValidationResult:
    def test_no_errors_no_warnings(self) -> None:
        r = ValidationResult(is_valid=True)
        assert r.is_valid
        assert not r.has_errors()
        assert not r.has_warnings()

    def test_with_errors(self) -> None:
        r = ValidationResult(is_valid=False, errors=["bad"])
        assert not r.is_valid
        assert r.has_errors()

    def test_with_warnings(self) -> None:
        r = ValidationResult(is_valid=True, warnings=["watch out"])
        assert r.is_valid
        assert r.has_warnings()
        assert not r.has_errors()


class TestValidateSlides:
    def test_all_files_exist(self, tmp_path: Path) -> None:
        s1 = tmp_path / "s1.tif"
        s2 = tmp_path / "s2.tif"
        s1.write_bytes(b"\x00" * 100)
        s2.write_bytes(b"\x00" * 100)

        out = tmp_path / "output"
        result = validate_slides([s1, s2], out)
        assert result.is_valid

    def test_missing_file_produces_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.tif"
        out = tmp_path / "output"

        result = validate_slides([missing], out)
        assert result.has_errors()
        assert any("not found" in e for e in result.errors)

    def test_unsupported_extension_produces_warning(self, tmp_path: Path) -> None:
        f = tmp_path / "file.bmp"
        f.write_bytes(b"\x00" * 100)
        out = tmp_path / "output"

        result = validate_slides([f], out)
        # .bmp is not in supported_extensions → warning
        assert result.has_warnings()

    def test_output_dir_created(self, tmp_path: Path) -> None:
        f = tmp_path / "slide.tif"
        f.write_bytes(b"\x00" * 100)
        out = tmp_path / "nested" / "output"

        result = validate_slides([f], out)
        assert result.is_valid
        assert out.exists()

    def test_empty_slide_list(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        result = validate_slides([], out)
        # No missing files → valid
        assert result.is_valid
