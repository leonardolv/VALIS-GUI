"""Tests for the VALIS pipeline configuration mapping."""

from __future__ import annotations

from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import build_registrar_kwargs


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
