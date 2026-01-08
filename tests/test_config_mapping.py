from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import build_registrar_kwargs


def test_build_registrar_kwargs_maps_config() -> None:
    config = Config(
        project_name="Example",
        rigid_registration=False,
        non_rigid_registration=True,
        max_image_size=4096,
        match_threshold=0.5,
        use_gpu=True,
    )

    kwargs = build_registrar_kwargs(config)

    assert kwargs == {
        "rigid_registrar": False,
        "non_rigid_registrar": True,
        "max_image_size": 4096,
        "match_threshold": 0.5,
        "use_gpu": True,
    }
