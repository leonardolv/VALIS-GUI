"""Tests for constants module."""

from __future__ import annotations

from valis_workstation.constants import (
    ConfigKeys,
    CropModes,
    FeatureDetectors,
    ImageFormats,
    TransformerTypes,
    compression_level_to_method,
)


class TestFeatureDetectors:
    def test_all_returns_list(self) -> None:
        result = FeatureDetectors.all()
        assert isinstance(result, list)
        assert len(result) >= 6

    def test_known_detectors_present(self) -> None:
        detectors = FeatureDetectors.all()
        assert FeatureDetectors.VGG in detectors
        assert FeatureDetectors.SUPERPOINT in detectors
        assert FeatureDetectors.DEDODE in detectors

    def test_class_attributes_match_list(self) -> None:
        all_dets = FeatureDetectors.all()
        assert FeatureDetectors.VGG == "vgg"
        assert FeatureDetectors.BRISK == "brisk"
        for det in all_dets:
            assert isinstance(det, str)

    def test_label_roundtrip(self) -> None:
        for key in FeatureDetectors.all():
            label = FeatureDetectors.label_for(key)
            assert FeatureDetectors.key_for_label(label) == key


class TestTransformerTypes:
    def test_all_returns_three(self) -> None:
        result = TransformerTypes.all()
        assert len(result) == 3

    def test_known_types(self) -> None:
        types = TransformerTypes.all()
        assert "affine" in types
        assert "rigid" in types
        assert "similarity" in types

    def test_label_roundtrip(self) -> None:
        for key in TransformerTypes.all():
            label = TransformerTypes.label_for(key)
            assert TransformerTypes.key_for_label(label) == key


class TestCropModes:
    def test_all_returns_four(self) -> None:
        result = CropModes.all()
        assert len(result) == 4

    def test_known_modes(self) -> None:
        modes = CropModes.all()
        assert "reference" in modes
        assert "all_overlap" in modes
        assert "all" in modes
        assert "unchanged" in modes


class TestImageFormats:
    def test_all(self) -> None:
        result = ImageFormats.all()
        assert "OME-TIFF" in result
        assert "TIFF" in result


class TestConfigKeys:
    def test_basic_keys_exist(self) -> None:
        assert ConfigKeys.PROJECT_NAME == "project_name"
        assert ConfigKeys.RIGID_REGISTRATION == "rigid_registration"
        assert ConfigKeys.USE_GPU == "use_gpu"

    def test_advanced_keys_exist(self) -> None:
        assert ConfigKeys.FEATURE_DETECTOR == "feature_detector"
        assert ConfigKeys.CROP_MODE == "crop_mode"
        assert ConfigKeys.MICRO_REGISTRATION == "micro_registration"


class TestCompressionLevelToMethod:
    """Regression tests for the ``compression_level`` (0-9 int) -> VALIS/
    pyvips ``compression`` (method-name str) mapping.

    Before this existed, ``services/valis_pipeline.py`` and
    ``services/merge_slides.py`` both passed ``Config.compression_level``
    straight through as VALIS's ``compression`` keyword, which
    ``valis.slide_io.save_ome_tiff`` unconditionally calls ``.lower()`` on
    before handing to ``pyvips.Image.tiffsave`` - crashing every real save
    with ``AttributeError: 'int' object has no attribute 'lower'``.
    """

    # The only method names pyvips's TIFF writer actually accepts, per
    # ``pyvips.enums.ForeignTiffCompression``.
    _VALID_METHODS = {
        "none",
        "jpeg",
        "deflate",
        "packbits",
        "ccittfax4",
        "lzw",
        "webp",
        "zstd",
        "jp2k",
    }

    def test_returns_a_string_for_every_valid_level(self) -> None:
        for level in range(10):
            method = compression_level_to_method(level)
            assert isinstance(method, str)
            # This is the exact call `save_ome_tiff` makes on the value -
            # if it ever raised here again, that's the regression.
            method.lower()

    def test_every_level_maps_to_a_method_pyvips_actually_supports(self) -> None:
        for level in range(10):
            assert compression_level_to_method(level) in self._VALID_METHODS

    def test_level_zero_is_no_compression(self) -> None:
        assert compression_level_to_method(0) == "none"

    def test_level_nine_is_maximum_not_fastest(self) -> None:
        # "9 = Maximum compression (slowest, smallest)" per the Save
        # Options/Properties dock tooltip - must not resolve to "none".
        assert compression_level_to_method(9) == "deflate"

    def test_out_of_range_values_are_clamped_not_raised(self) -> None:
        assert compression_level_to_method(-5) == compression_level_to_method(0)
        assert compression_level_to_method(99) == compression_level_to_method(9)

    def test_monotonic_family_low_levels_are_lzw_high_levels_are_deflate(self) -> None:
        # Not a strict requirement of the mapping, but documents the
        # intended "fast -> thorough" progression the tooltip describes.
        assert compression_level_to_method(1) == "lzw"
        assert compression_level_to_method(5) == "deflate"
