"""Tests for the VALIS pipeline configuration mapping."""

from __future__ import annotations

from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import (
    build_registrar_kwargs,
    build_save_kwargs,
)


class TestBuildRegistrarKwargs:
    def test_basic_mapping(self) -> None:
        config = Config(
            rigid_registration=False,
            non_rigid_registration=True,
            max_image_size=4096,
        )
        kwargs = build_registrar_kwargs(config)
        assert kwargs["max_image_dim_px"] == 4096
        assert kwargs["do_rigid"] is False

    def test_non_rigid_disabled(self) -> None:
        config = Config(non_rigid_registration=False)
        kwargs = build_registrar_kwargs(config)
        # When non-rigid is disabled, registrar_cls should be None/absent
        assert (
            kwargs.get("non_rigid_registrar_cls") is None
            or "non_rigid_registrar_cls" not in kwargs
            or kwargs.get("non_rigid_registrar_cls") is None
        )

    def test_non_rigid_enabled(self) -> None:
        config = Config(non_rigid_registration=True)
        kwargs = build_registrar_kwargs(config)
        assert "non_rigid_registrar_cls" in kwargs

    def test_custom_max_size(self) -> None:
        config = Config(max_image_size=8192)
        kwargs = build_registrar_kwargs(config)
        assert kwargs["max_image_dim_px"] == 8192

    def test_transformer_cls_scikit_image_import_error_fallback(self, monkeypatch) -> None:
        from valis_workstation.services.valis_pipeline import _get_transformer_cls
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "skimage" or name.startswith("skimage."):
                raise ImportError("Mocked missing scikit-image")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        fallback_cls = _get_transformer_cls("similarity")
        assert fallback_cls is not None
        assert fallback_cls.__name__ == "SimilarityTransform"


class TestBuildSaveKwargs:
    """Regression tests for the ``compression`` kwarg `run_valis_pipeline`
    passes to `Valis.warp_and_save_slides`.

    Before this, `compression_level` (a 0-9 int from the Save Options
    dialog/Properties dock) was forwarded verbatim as `compression`, which
    `valis.slide_io.save_ome_tiff` calls `.lower()` on before handing to
    `pyvips.Image.tiffsave` - crashing every real registration save with
    `AttributeError: 'int' object has no attribute 'lower'`.
    """

    def test_compression_is_a_lowercase_method_string_not_the_raw_int(self) -> None:
        config = Config(compression_level=6)
        kwargs = build_save_kwargs(config)
        assert kwargs["compression"] == "deflate"
        assert isinstance(kwargs["compression"], str)

    def test_default_compression_level_does_not_crash(self) -> None:
        # Config()'s own default (1) is what every un-touched Save Options
        # dialog/Properties dock ships with.
        config = Config()
        kwargs = build_save_kwargs(config)
        assert kwargs["compression"] == "lzw"

    def test_zero_maps_to_none_compression(self) -> None:
        config = Config(compression_level=0)
        kwargs = build_save_kwargs(config)
        assert kwargs["compression"] == "none"

    def test_pyramid_tile_and_quality_pass_through_unchanged(self) -> None:
        config = Config(
            write_pyramid=False, tile_size=256, image_quality=80, compression_level=3
        )
        kwargs = build_save_kwargs(config)
        assert kwargs["pyramid"] is False
        assert kwargs["tile_wh"] == 256
        assert kwargs["Q"] == 80

    def test_zero_quality_is_omitted_like_before(self) -> None:
        config = Config(image_quality=0)
        # Config.__post_init__ clamps to >= 1, so simulate the "falsy"
        # branch directly to pin the existing `> 0` guard's behaviour.
        config.image_quality = 0
        kwargs = build_save_kwargs(config)
        assert "Q" not in kwargs
