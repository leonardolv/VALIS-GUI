"""Tests for ``services/merge_slides.py``, in particular the "Normalize
intensities" option that ``MergeSlidesDialog`` exposes.

Before this fix, ``MergeSlidesDialog.get_merge_config()["normalize"]`` was
read into ``merge_config`` and then never consulted anywhere in
``merge_registered_slides`` - the checkbox had no effect regardless of its
state. These tests exercise the real service function end to end using a
lightweight fake that mimics the subset of the ``pyvips.Image`` API this
module relies on (band indexing, ``min``/``max``, arithmetic, ``cast``,
``bandjoin``), since ``pyvips``/VALIS's full scientific stack isn't
installed in this environment.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from valis_workstation.services.merge_slides import (
    _normalize_channels,
    merge_registered_slides,
)
from valis_workstation.utils.exceptions import UserVisibleError


class FakeVipsImage:
    """Minimal stand-in for ``pyvips.Image`` covering what this module uses."""

    def __init__(self, band_values, fmt="uchar", width=4, height=4):
        # Normalize to "list of bands, each a flat list of pixel values".
        if band_values and isinstance(band_values[0], (int, float)):
            band_values = [band_values]
        self._band_values = [list(b) for b in band_values]
        self.format = fmt
        self.width = width
        self.height = height

    @property
    def bands(self):
        return len(self._band_values)

    def __getitem__(self, idx):
        return FakeVipsImage(
            [self._band_values[idx]], fmt=self.format, width=self.width, height=self.height
        )

    def min(self):
        return min(self._band_values[0])

    def max(self):
        return max(self._band_values[0])

    def __sub__(self, scalar):
        return FakeVipsImage(
            [[v - scalar for v in self._band_values[0]]],
            fmt=self.format,
            width=self.width,
            height=self.height,
        )

    def __mul__(self, scalar):
        return FakeVipsImage(
            [[v * scalar for v in self._band_values[0]]],
            fmt=self.format,
            width=self.width,
            height=self.height,
        )

    def cast(self, fmt):
        self.format = fmt
        return self

    def bandjoin(self, others):
        if not isinstance(others, list):
            others = [others]
        combined = list(self._band_values)
        for other in others:
            combined.extend(other._band_values)
        return FakeVipsImage(combined, fmt=self.format, width=self.width, height=self.height)


# ---------------------------------------------------------------------------
# _normalize_channels
# ---------------------------------------------------------------------------


class TestNormalizeChannels:
    def test_stretches_a_single_band_to_full_range(self):
        img = FakeVipsImage([10, 20, 30], fmt="uchar")
        result = _normalize_channels(img)
        assert result.format == "uchar"
        assert result._band_values[0] == pytest.approx([0, 127.5, 255])

    def test_each_band_is_stretched_independently(self):
        # Band 0 spans [0, 100], band 1 spans [50, 150] - very different
        # ranges, so a shared (non-per-channel) stretch would get this wrong.
        img = FakeVipsImage([[0, 100], [50, 150]], fmt="ushort")
        result = _normalize_channels(img)
        assert result.bands == 2
        assert result._band_values[0] == pytest.approx([0, 65535])
        assert result._band_values[1] == pytest.approx([0, 65535])

    def test_flat_band_is_left_unchanged_not_divided_by_zero(self):
        img = FakeVipsImage([42, 42, 42], fmt="uchar")
        result = _normalize_channels(img)
        # No exception, and the (meaningless-to-stretch) flat values survive.
        assert result._band_values[0] == [42, 42, 42]

    def test_unsupported_format_is_returned_unchanged(self, caplog):
        img = FakeVipsImage([0.1, 0.5, 0.9], fmt="float")
        result = _normalize_channels(img)
        assert result is img
        assert "unsupported pixel format" in caplog.text


# ---------------------------------------------------------------------------
# merge_registered_slides
# ---------------------------------------------------------------------------


def _base_merge_config(normalize: bool) -> dict:
    return {
        "channels": [
            {"slide_name": "slide_a.tiff", "channel_name": "DAPI", "color": "Auto"},
            {"slide_name": "slide_b.tiff", "channel_name": "GFP", "color": "Auto"},
        ],
        "duplicate_handling": "average",
        "output_name": "merged_image",
        "normalize": normalize,
    }


class TestMergeRegisteredSlidesNormalizeFlag:
    def test_normalize_false_saves_directly_via_valis_unchanged(self, tmp_path):
        """The pre-existing, already-tested-in-production path: VALIS is
        asked to save the file itself, and this module never touches pixels
        or imports valis.slide_io."""
        registrar = MagicMock()
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([1, 2, 3]),
            ["DAPI", "GFP"],
            "<OME/>",
        )

        result = merge_registered_slides(
            registrar=registrar,
            merge_config=_base_merge_config(normalize=False),
            output_path=tmp_path,
        )

        assert result == tmp_path / "merged_image.ome.tiff"
        registrar.warp_and_merge_slides.assert_called_once()
        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["dst_f"] == str(result)
        # No call to get_ref_slide - the normalize branch never runs.
        registrar.get_ref_slide.assert_not_called()

    def test_normalize_true_builds_stretches_and_saves_via_slide_io(
        self, tmp_path, monkeypatch
    ):
        registrar = MagicMock()
        merged_img = FakeVipsImage([[0, 100], [10, 60]], fmt="uchar")
        registrar.warp_and_merge_slides.return_value = (
            merged_img,
            ["DAPI", "GFP"],
            "<OME/>",
        )
        ref_slide = MagicMock()
        ref_slide.reader = MagicMock()
        registrar.get_ref_slide.return_value = ref_slide

        fake_slide_io = types.SimpleNamespace(
            get_tile_wh=MagicMock(return_value=512),
            save_ome_tiff=MagicMock(),
        )
        monkeypatch.setitem(sys.modules, "valis.slide_io", fake_slide_io)
        monkeypatch.setitem(sys.modules, "valis", types.SimpleNamespace())

        result = merge_registered_slides(
            registrar=registrar,
            merge_config=_base_merge_config(normalize=True),
            output_path=tmp_path,
        )

        assert result == tmp_path / "merged_image.ome.tiff"

        # VALIS was asked to build the image WITHOUT saving it itself.
        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["dst_f"] is None

        # The saved image is the normalized one, written by slide_io directly.
        fake_slide_io.save_ome_tiff.assert_called_once()
        save_args, save_kwargs = fake_slide_io.save_ome_tiff.call_args
        saved_img = save_args[0]
        assert saved_img._band_values[0] == pytest.approx([0, 255])
        assert saved_img._band_values[1] == pytest.approx([0, 255])
        assert save_kwargs["dst_f"] == str(result)
        assert save_kwargs["ome_xml"] == "<OME/>"
        assert save_kwargs["tile_wh"] == 512
        fake_slide_io.get_tile_wh.assert_called_once_with(
            reader=ref_slide.reader, level=0, out_shape_wh=(4, 4)
        )

    def test_normalize_true_respects_explicit_tile_size_without_asking_valis(
        self, tmp_path, monkeypatch
    ):
        registrar = MagicMock()
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([0, 255]),
            ["DAPI"],
            "<OME/>",
        )
        fake_slide_io = types.SimpleNamespace(
            get_tile_wh=MagicMock(return_value=999),
            save_ome_tiff=MagicMock(),
        )
        monkeypatch.setitem(sys.modules, "valis.slide_io", fake_slide_io)
        monkeypatch.setitem(sys.modules, "valis", types.SimpleNamespace())

        merge_registered_slides(
            registrar=registrar,
            merge_config=_base_merge_config(normalize=True),
            output_path=tmp_path,
            save_config={"tile_size": 256},
        )

        fake_slide_io.get_tile_wh.assert_not_called()
        _, save_kwargs = fake_slide_io.save_ome_tiff.call_args
        assert save_kwargs["tile_wh"] == 256

    def test_normalize_true_cancelled_after_build_raises_and_never_saves(
        self, tmp_path, monkeypatch
    ):
        registrar = MagicMock()
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([0, 255]),
            ["DAPI"],
            "<OME/>",
        )
        fake_slide_io = types.SimpleNamespace(
            get_tile_wh=MagicMock(return_value=512),
            save_ome_tiff=MagicMock(),
        )
        monkeypatch.setitem(sys.modules, "valis.slide_io", fake_slide_io)
        monkeypatch.setitem(sys.modules, "valis", types.SimpleNamespace())

        calls = {"n": 0}

        def cancel_check():
            calls["n"] += 1
            # Not cancelled the first time (before the build), cancelled the
            # second (right after) - proves the post-build check is real.
            return calls["n"] > 1

        with pytest.raises(UserVisibleError, match="cancelled"):
            merge_registered_slides(
                registrar=registrar,
                merge_config=_base_merge_config(normalize=True),
                output_path=tmp_path,
                cancel_check=cancel_check,
            )

        fake_slide_io.save_ome_tiff.assert_not_called()

    def test_progress_callback_reaches_100_for_both_paths(self, tmp_path, monkeypatch):
        fake_slide_io = types.SimpleNamespace(
            get_tile_wh=MagicMock(return_value=512),
            save_ome_tiff=MagicMock(),
        )
        monkeypatch.setitem(sys.modules, "valis.slide_io", fake_slide_io)
        monkeypatch.setitem(sys.modules, "valis", types.SimpleNamespace())

        for normalize in (False, True):
            registrar = MagicMock()
            registrar.warp_and_merge_slides.return_value = (
                FakeVipsImage([0, 255]),
                ["DAPI"],
                "<OME/>",
            )
            progress_values = []
            merge_registered_slides(
                registrar=registrar,
                merge_config=_base_merge_config(normalize=normalize),
                output_path=tmp_path,
                progress_callback=progress_values.append,
            )
            assert progress_values[-1] == 100
