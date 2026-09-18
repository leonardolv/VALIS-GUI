"""Tests for ``services/merge_slides.py``, in particular the "Normalize
intensities" option and the per-channel "Color" picker that
``MergeSlidesDialog`` exposes.

Before the normalize fix, ``MergeSlidesDialog.get_merge_config()["normalize"]``
was read into ``merge_config`` and then never consulted anywhere in
``merge_registered_slides`` - the checkbox had no effect regardless of its
state. Before the color fix, each channel's ``"color"`` field (from the
dialog's per-row combo box) was collected the same way and likewise never
read - every merge used VALIS's own automatic per-channel colors regardless
of what a user picked. These tests exercise the real service function end
to end using a lightweight fake that mimics the subset of the
``pyvips.Image`` API this module relies on (band indexing, ``min``/``max``,
arithmetic, ``cast``, ``bandjoin``), since ``pyvips``/VALIS's full
scientific stack isn't installed in this environment.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from valis_workstation.services.merge_slides import (
    _keep_last_occurrence,
    _normalize_channels,
    _resolve_channel_colormap,
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

# ---------------------------------------------------------------------------
# _resolve_channel_colormap
# ---------------------------------------------------------------------------


class TestResolveChannelColormap:
    def test_all_auto_returns_none(self):
        channels = [
            {"slide_name": "a.tiff", "channel_name": "DAPI", "color": "Auto"},
            {"slide_name": "b.tiff", "channel_name": "GFP", "color": "Auto"},
        ]
        assert _resolve_channel_colormap(channels) is None

    def test_all_explicit_builds_a_full_dict_without_importing_slide_io(
        self, monkeypatch
    ):
        # No valis/valis.slide_io in sys.modules at all - if this needed to
        # import it (it shouldn't, since nothing is left on "Auto"), it
        # would raise ImportError and fail the test.
        monkeypatch.delitem(sys.modules, "valis.slide_io", raising=False)
        monkeypatch.delitem(sys.modules, "valis", raising=False)

        channels = [
            {"slide_name": "a.tiff", "channel_name": "DAPI", "color": "Blue"},
            {"slide_name": "b.tiff", "channel_name": "GFP", "color": "Green"},
        ]
        result = _resolve_channel_colormap(channels)
        assert result == {"DAPI": (0, 0, 255), "GFP": (0, 255, 0)}

    def test_mixed_auto_and_explicit_fills_auto_slots_via_slide_io(
        self, monkeypatch
    ):
        fake_slide_io = types.SimpleNamespace(
            get_colormap=MagicMock(return_value={"GFP": (7, 8, 9)})
        )
        monkeypatch.setitem(sys.modules, "valis.slide_io", fake_slide_io)
        monkeypatch.setitem(sys.modules, "valis", types.SimpleNamespace())

        channels = [
            {"slide_name": "a.tiff", "channel_name": "DAPI", "color": "Red"},
            {"slide_name": "b.tiff", "channel_name": "GFP", "color": "Auto"},
        ]
        result = _resolve_channel_colormap(channels)

        # The explicit choice wins for DAPI; the "Auto" slot (GFP) is filled
        # in via VALIS's own auto-assignment rather than left out entirely
        # (which would make Valis.warp_and_merge_slides's dict-colormap
        # validation reject the whole thing for a missing channel name).
        fake_slide_io.get_colormap.assert_called_once_with(["GFP"], is_rgb=False)
        assert result == {"DAPI": (255, 0, 0), "GFP": (7, 8, 9)}

    def test_mixed_falls_back_to_white_when_slide_io_is_unavailable(
        self, monkeypatch, caplog
    ):
        monkeypatch.delitem(sys.modules, "valis.slide_io", raising=False)
        monkeypatch.delitem(sys.modules, "valis", raising=False)

        channels = [
            {"slide_name": "a.tiff", "channel_name": "DAPI", "color": "Red"},
            {"slide_name": "b.tiff", "channel_name": "GFP", "color": "Auto"},
        ]
        result = _resolve_channel_colormap(channels)

        assert result == {"DAPI": (255, 0, 0), "GFP": (255, 255, 255)}
        assert "Could not auto-assign colors" in caplog.text

    def test_unknown_color_value_is_treated_as_auto(self):
        # Defensive: an unrecognized string (e.g. a stale config from a
        # future dialog version) should behave like "Auto", not raise.
        channels = [
            {"slide_name": "a.tiff", "channel_name": "DAPI", "color": "Not A Color"},
        ]
        assert _resolve_channel_colormap(channels) is None


# ---------------------------------------------------------------------------
# merge_registered_slides + colormap
# ---------------------------------------------------------------------------


def _merge_config_with_colors(colors: list[str], normalize: bool = False) -> dict:
    names = ["DAPI", "GFP", "RFP"]
    return {
        "channels": [
            {
                "slide_name": f"slide_{i}.tiff",
                "channel_name": names[i],
                "color": colors[i],
            }
            for i in range(len(colors))
        ],
        "duplicate_handling": "average",
        "output_name": "merged_image",
        "normalize": normalize,
    }


class TestMergeRegisteredSlidesColormap:
    def test_all_auto_does_not_pass_a_colormap_kwarg(self, tmp_path):
        """Preserves VALIS's own default (auto-assigned) exactly - no
        equivalent-but-different override when nothing was actually chosen."""
        registrar = MagicMock()
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([1, 2, 3]),
            ["DAPI", "GFP"],
            "<OME/>",
        )
        merge_registered_slides(
            registrar=registrar,
            merge_config=_merge_config_with_colors(["Auto", "Auto"]),
            output_path=tmp_path,
        )
        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert "colormap" not in called_kwargs

    def test_explicit_colors_reach_warp_and_merge_slides(self, tmp_path):
        registrar = MagicMock()
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([1, 2, 3]),
            ["DAPI", "GFP"],
            "<OME/>",
        )
        merge_registered_slides(
            registrar=registrar,
            merge_config=_merge_config_with_colors(["Blue", "Green"]),
            output_path=tmp_path,
        )
        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["colormap"] == {"DAPI": (0, 0, 255), "GFP": (0, 255, 0)}

    def test_explicit_colors_also_reach_the_normalize_build_call(
        self, tmp_path, monkeypatch
    ):
        """The normalize path builds the image via a separate,
        `dst_f=None` call - the colormap must still be forwarded there,
        since that's what actually gets embedded into the returned OME-XML."""
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

        merge_registered_slides(
            registrar=registrar,
            merge_config=_merge_config_with_colors(["Blue", "Green"], normalize=True),
            output_path=tmp_path,
        )

        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["dst_f"] is None
        assert called_kwargs["colormap"] == {"DAPI": (0, 0, 255), "GFP": (0, 255, 0)}


class TestMergeRegisteredSlidesSlideSelection:
    """Before this fix, `selected_slides` (the slide names still checked in
    MergeSlidesDialog's "Include" column, also driven by its "Select
    All"/"Select None" buttons) was computed and then never used -
    `merge_kwargs` never set `src_f_list`, so
    `Valis.warp_and_merge_slides` fell back to its own default of *every*
    slide in the registrar, regardless of what the user unchecked. Worse,
    since `channel_name_dict` (which IS built from only the checked rows)
    has no entry for an unchecked slide, a real merge with any slide
    unchecked would have raised a bare `KeyError` from inside VALIS the
    moment it reached that slide.
    """

    @staticmethod
    def _registrar_with_slides(**src_f_by_name: str) -> MagicMock:
        registrar = MagicMock()
        registrar.slide_dict = {
            name: types.SimpleNamespace(src_f=src_f)
            for name, src_f in src_f_by_name.items()
        }
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([1, 2, 3]),
            ["DAPI", "CY5"],
            "<OME/>",
        )
        return registrar

    def test_only_checked_slides_reach_src_f_list(self, tmp_path):
        registrar = self._registrar_with_slides(
            **{
                "slide_a.tiff": "/data/slide_a.tiff",
                "slide_b.tiff": "/data/slide_b.tiff",
                "slide_c.tiff": "/data/slide_c.tiff",
            }
        )
        merge_config = {
            "channels": [
                {"slide_name": "slide_a.tiff", "channel_name": "DAPI", "color": "Auto"},
                # slide_b.tiff deliberately absent - its "Include" checkbox
                # was unchecked in the dialog.
                {"slide_name": "slide_c.tiff", "channel_name": "CY5", "color": "Auto"},
            ],
            "duplicate_handling": "average",
            "output_name": "merged_image",
            "normalize": False,
        }

        merge_registered_slides(
            registrar=registrar, merge_config=merge_config, output_path=tmp_path
        )

        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["src_f_list"] == [
            "/data/slide_a.tiff",
            "/data/slide_c.tiff",
        ]
        # The excluded slide must not appear in the channel mapping either.
        assert "slide_b.tiff" not in called_kwargs["channel_name_dict"]

    def test_all_slides_checked_still_passes_an_explicit_src_f_list(self, tmp_path):
        """Even the "nothing was deselected" case must pass `src_f_list`
        explicitly - relying on VALIS's own default is exactly the bug,
        and would silently reintroduce it the moment any user unchecks a
        row in a future run."""
        registrar = self._registrar_with_slides(
            **{
                "slide_a.tiff": "/data/slide_a.tiff",
                "slide_b.tiff": "/data/slide_b.tiff",
            }
        )

        merge_registered_slides(
            registrar=registrar,
            merge_config=_base_merge_config(normalize=False),
            output_path=tmp_path,
        )

        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["src_f_list"] == [
            "/data/slide_a.tiff",
            "/data/slide_b.tiff",
        ]

    def test_a_slide_missing_from_the_registrar_raises_instead_of_crashing_valis(
        self, tmp_path
    ):
        """A defensive guard: if a checked slide somehow isn't in the
        registrar any more, fail with a clear `UserVisibleError` before
        ever calling into VALIS, rather than a bare `KeyError` surfacing
        from inside `warp_and_merge_slides`."""
        registrar = self._registrar_with_slides(**{"slide_a.tiff": "/data/slide_a.tiff"})

        with pytest.raises(UserVisibleError):
            merge_registered_slides(
                registrar=registrar,
                merge_config=_base_merge_config(normalize=False),
                output_path=tmp_path,
            )

        registrar.warp_and_merge_slides.assert_not_called()

    def test_src_f_list_also_reaches_the_normalize_build_call(
        self, tmp_path, monkeypatch
    ):
        registrar = self._registrar_with_slides(
            **{
                "slide_a.tiff": "/data/slide_a.tiff",
                "slide_b.tiff": "/data/slide_b.tiff",
            }
        )
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

        merge_registered_slides(
            registrar=registrar,
            merge_config=_base_merge_config(normalize=True),
            output_path=tmp_path,
        )

        called_kwargs = registrar.warp_and_merge_slides.call_args.kwargs
        assert called_kwargs["dst_f"] is None
        assert called_kwargs["src_f_list"] == [
            "/data/slide_a.tiff",
            "/data/slide_b.tiff",
        ]


class TestKeepLastOccurrence:
    """Unit tests for `_keep_last_occurrence`, the helper that resolves
    "Last" duplicate handling by dropping the earlier slide(s) sharing a
    duplicate channel name."""

    def test_no_duplicates_returns_the_list_unchanged(self):
        selected = ["a.tiff", "b.tiff", "c.tiff"]
        channel_name_dict = {
            "a.tiff": ["DAPI"],
            "b.tiff": ["GFP"],
            "c.tiff": ["CY5"],
        }
        assert _keep_last_occurrence(selected, channel_name_dict) == selected

    def test_two_slides_sharing_a_name_keeps_only_the_later_one(self):
        selected = ["a.tiff", "b.tiff"]
        channel_name_dict = {"a.tiff": ["DAPI"], "b.tiff": ["DAPI"]}
        assert _keep_last_occurrence(selected, channel_name_dict) == ["b.tiff"]

    def test_non_adjacent_duplicate_preserves_relative_order_of_survivors(self):
        # "DAPI" appears on a.tiff and c.tiff - only c.tiff (the later one)
        # should survive; b.tiff (a unique name) is untouched and keeps its
        # original position relative to the survivors.
        selected = ["a.tiff", "b.tiff", "c.tiff"]
        channel_name_dict = {
            "a.tiff": ["DAPI"],
            "b.tiff": ["GFP"],
            "c.tiff": ["DAPI"],
        }
        assert _keep_last_occurrence(selected, channel_name_dict) == [
            "b.tiff",
            "c.tiff",
        ]

    def test_three_way_duplicate_keeps_only_the_last(self):
        selected = ["a.tiff", "b.tiff", "c.tiff"]
        channel_name_dict = {
            "a.tiff": ["DAPI"],
            "b.tiff": ["DAPI"],
            "c.tiff": ["DAPI"],
        }
        assert _keep_last_occurrence(selected, channel_name_dict) == ["c.tiff"]


class TestMergeRegisteredSlidesLastDuplicateHandling:
    """Before this fix, "Last" duplicate handling was byte-for-byte
    identical to "First": both set `drop_duplicates=True` on VALIS's side
    and nothing ever reordered or filtered anything despite the code's own
    log message claiming "'last' handling will use reverse order". Selecting
    "Last" in the dialog therefore always produced the exact same merge as
    "First", regardless of which slide the user actually expected to win for
    a duplicate channel name.
    """

    @staticmethod
    def _registrar_with_slides(**src_f_by_name: str) -> MagicMock:
        registrar = MagicMock()
        registrar.slide_dict = {
            name: types.SimpleNamespace(src_f=src_f)
            for name, src_f in src_f_by_name.items()
        }
        registrar.warp_and_merge_slides.return_value = (
            FakeVipsImage([1, 2, 3]),
            ["DAPI"],
            "<OME/>",
        )
        return registrar

    @staticmethod
    def _duplicate_dapi_config(duplicate_handling: str) -> dict:
        return {
            "channels": [
                {"slide_name": "round1.tiff", "channel_name": "DAPI", "color": "Auto"},
                {"slide_name": "round2.tiff", "channel_name": "GFP", "color": "Auto"},
                {"slide_name": "round3.tiff", "channel_name": "DAPI", "color": "Auto"},
            ],
            "duplicate_handling": duplicate_handling,
            "output_name": "merged_image",
            "normalize": False,
        }

    def _run(self, tmp_path, duplicate_handling: str) -> dict:
        registrar = self._registrar_with_slides(
            **{
                "round1.tiff": "/data/round1.tiff",
                "round2.tiff": "/data/round2.tiff",
                "round3.tiff": "/data/round3.tiff",
            }
        )
        merge_registered_slides(
            registrar=registrar,
            merge_config=self._duplicate_dapi_config(duplicate_handling),
            output_path=tmp_path,
        )
        return registrar.warp_and_merge_slides.call_args.kwargs

    def test_last_keeps_the_later_duplicate_slide_not_the_earlier_one(
        self, tmp_path
    ):
        called_kwargs = self._run(tmp_path, "last")

        # round1.tiff (the earlier "DAPI") must be dropped; round3.tiff (the
        # later one) and the uniquely-named round2.tiff must survive, in
        # their original relative order.
        assert called_kwargs["src_f_list"] == [
            "/data/round2.tiff",
            "/data/round3.tiff",
        ]
        assert "round1.tiff" not in called_kwargs["channel_name_dict"]
        assert called_kwargs["channel_name_dict"]["round3.tiff"] == ["DAPI"]
        # Duplicates were already resolved by dropping round1.tiff above, so
        # there's nothing left for VALIS's own flag to drop.
        assert called_kwargs["drop_duplicates"] is False

    def test_first_keeps_the_earlier_duplicate_slide_not_the_later_one(
        self, tmp_path
    ):
        called_kwargs = self._run(tmp_path, "first")

        assert called_kwargs["src_f_list"] == [
            "/data/round1.tiff",
            "/data/round2.tiff",
            "/data/round3.tiff",
        ]
        assert "round1.tiff" in called_kwargs["channel_name_dict"]
        assert called_kwargs["drop_duplicates"] is True

    def test_first_and_last_now_produce_different_results(self, tmp_path):
        """The regression this fix closes: before it, "first" and "last"
        passed the identical `src_f_list`/`drop_duplicates` to VALIS for the
        same input - selecting "Last" had no observable effect at all."""
        first_kwargs = self._run(tmp_path, "first")
        last_kwargs = self._run(tmp_path, "last")

        assert first_kwargs["src_f_list"] != last_kwargs["src_f_list"]
