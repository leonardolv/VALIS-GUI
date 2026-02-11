"""Tests for data models (Config dataclass)."""
from __future__ import annotations

from dataclasses import asdict
from valis_workstation.models.config import Config


class TestConfigDefaults:
    def test_default_values(self) -> None:
        c = Config()
        assert c.project_name == "New Project"
        assert c.rigid_registration is True
        assert c.non_rigid_registration is True
        assert c.max_image_size == 2048
        assert c.use_gpu is False

    def test_advanced_defaults(self) -> None:
        c = Config()
        assert c.feature_detector == "vgg"
        assert c.transformer_type == "similarity"
        assert c.reference_slide is None
        assert c.crop_mode == "reference"
        assert c.use_masks is False
        assert c.denoise is False
        assert c.imgs_ordered is False
        assert c.micro_registration is False
        assert c.micro_max_image_size == 4096

    def test_save_defaults(self) -> None:
        c = Config()
        assert c.compression_level == 1
        assert c.pyramid_levels == 4
        assert c.tile_size == 512
        assert c.image_quality == 95


class TestConfigCustom:
    def test_custom_values(self) -> None:
        c = Config(
            project_name="Test",
            rigid_registration=False,
            max_image_size=4096,
            feature_detector="kaze",
            micro_registration=True,
        )
        assert c.project_name == "Test"
        assert c.rigid_registration is False
        assert c.max_image_size == 4096
        assert c.feature_detector == "kaze"
        assert c.micro_registration is True

    def test_asdict_roundtrip(self) -> None:
        c = Config(project_name="Round", use_gpu=True)
        d = asdict(c)
        c2 = Config(**d)
        assert c == c2

    def test_all_fields_present_in_dict(self) -> None:
        d = asdict(Config())
        expected_keys = {
            "project_name", "rigid_registration", "non_rigid_registration",
            "max_image_size", "use_gpu",
            "feature_detector", "transformer_type", "reference_slide",
            "crop_mode", "use_masks", "denoise", "imgs_ordered",
            "micro_registration", "micro_max_image_size",
            "compression_level", "pyramid_levels", "tile_size", "image_quality",
        }
        assert set(d.keys()) == expected_keys
