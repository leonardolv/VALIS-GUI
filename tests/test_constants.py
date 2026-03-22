"""Tests for constants module."""

from __future__ import annotations

from valis_workstation.constants import (
    ConfigKeys,
    CropModes,
    FeatureDetectors,
    ImageFormats,
    TransformerTypes,
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
