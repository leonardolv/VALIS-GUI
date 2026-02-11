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
        assert kwargs.get("non_rigid_registrar_cls") is None or \
               "non_rigid_registrar_cls" not in kwargs or \
               kwargs.get("non_rigid_registrar_cls") is None

    def test_non_rigid_enabled(self) -> None:
        config = Config(non_rigid_registration=True)
        kwargs = build_registrar_kwargs(config)
        assert "non_rigid_registrar_cls" in kwargs

    def test_custom_max_size(self) -> None:
        config = Config(max_image_size=8192)
        kwargs = build_registrar_kwargs(config)
        assert kwargs["max_image_dim_px"] == 8192
