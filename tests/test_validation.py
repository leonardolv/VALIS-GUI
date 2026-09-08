"""Tests for validation utilities."""

from __future__ import annotations

import shutil
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

    def test_disk_space_check_targets_output_dir_not_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The free-space check must probe output_dir's own filesystem, even
        when output_dir does not exist yet -- not fall back to the process's
        cwd, which can be an unrelated filesystem."""
        import valis_workstation.utils.validation as validation_module

        f = tmp_path / "slide.tif"
        f.write_bytes(b"\x00" * 100)

        # output_dir itself doesn't exist; its parent does.
        out = tmp_path / "not_yet_created" / "output"

        # Point cwd somewhere else entirely, so a wrong fallback would be
        # observably different from the correct target.
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        seen_paths = []
        real_disk_usage = shutil.disk_usage

        def _spy_disk_usage(path):
            seen_paths.append(Path(path))
            return real_disk_usage(path)

        monkeypatch.setattr(validation_module.shutil, "disk_usage", _spy_disk_usage)

        validate_slides([f], out)

        assert seen_paths, "disk_usage was never called"
        checked = seen_paths[0]
        assert checked != elsewhere.resolve()
        # The checked path must be an ancestor of (or equal to) output_dir,
        # i.e. somewhere under tmp_path -- not the unrelated cwd.
        assert tmp_path.resolve() in (checked, *checked.parents)
