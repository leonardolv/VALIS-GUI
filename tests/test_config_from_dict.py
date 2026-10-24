"""Config.from_dict must survive hand-edited or mistyped config files."""

from valis_workstation.models.config import Config


def test_valid_round_trip_has_no_problems():
    src = Config(project_name="p", max_image_size=1024, use_gpu=True)
    cfg, problems = Config.from_dict(
        {k: getattr(src, k) for k in Config.__dataclass_fields__}
    )
    assert cfg == src
    assert problems == []


def test_string_false_is_not_truthy():
    cfg, problems = Config.from_dict({"rigid_registration": "false", "use_gpu": "yes"})
    assert cfg.rigid_registration is False
    assert cfg.use_gpu is True
    assert problems == []


def test_numbers_are_coerced_or_ignored_not_raised():
    cfg, problems = Config.from_dict(
        {"max_image_size": "4096", "tile_size": 256.0, "image_quality": True,
         "compression_level": "abc", "pyramid_levels": None}
    )
    assert cfg.max_image_size == 4096
    assert cfg.tile_size == 256
    assert cfg.image_quality == Config().image_quality  # bool is not a number
    assert cfg.compression_level == Config().compression_level
    assert cfg.pyramid_levels == Config().pyramid_levels
    assert len(problems) == 3
    assert all(isinstance(getattr(cfg, k), int) for k in ("max_image_size", "tile_size"))


def test_bad_project_name_and_unknown_keys():
    cfg, problems = Config.from_dict({"project_name": None, "bogus": 1})
    assert cfg.project_name == Config().project_name
    assert any("bogus" in p for p in problems)
    cfg, problems = Config.from_dict({"project_name": "   "})
    assert cfg.project_name == Config().project_name
    assert problems


def test_non_object_json_gives_defaults():
    cfg, problems = Config.from_dict([1, 2])
    assert cfg == Config()
    assert problems


def test_reference_slide_may_be_null_or_string_only():
    assert Config.from_dict({"reference_slide": None})[0].reference_slide is None
    assert Config.from_dict({"reference_slide": "a.svs"})[0].reference_slide == "a.svs"
    cfg, problems = Config.from_dict({"reference_slide": 5})
    assert cfg.reference_slide is None and problems
