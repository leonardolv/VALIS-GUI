from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Config:
    """Registration configuration passed from the GUI to the VALIS pipeline.

    Every field here has a matching widget in :class:`PropertiesDock`.
    """

    # ── Basic settings ──────────────────────────────────────────────
    project_name: str = "New Project"
    rigid_registration: bool = True
    non_rigid_registration: bool = True
    max_image_size: int = 2048
    use_gpu: bool = False

    # ── Advanced settings ───────────────────────────────────────────
    feature_detector: str = "vgg"
    transformer_type: str = "similarity"  # similarity | affine | rigid
    reference_slide: str | None = None  # None ⇒ auto-detect
    crop_mode: str = "reference"
    use_masks: bool = False
    denoise: bool = False
    imgs_ordered: bool = False  # True ⇒ skip auto-sorting
    crop_for_rigid_reg: bool = True  # VALIS v1.2.0+: pre-crop before rigid
    use_color_features: bool = False  # VALIS v1.2.0+: RGB mode for deep detectors
    non_rigid_method: str = "optical_flow"  # optical_flow | raft

    # Micro-registration settings
    micro_registration: bool = False
    micro_max_image_size: int = 4096

    # ── Output / save settings ──────────────────────────────────────
    compression_level: int = 1  # 0 - 9
    pyramid_levels: int = 4
    tile_size: int = 512
    image_quality: int = 95  # JPEG quality 1 - 100
    image_format: str = "OME-TIFF"  # OME-TIFF | TIFF | JPEG | PNG
    write_pyramid: bool = True  # False ⇒ flat (non-pyramid) output

    def __post_init__(self) -> None:
        self.project_name = self.project_name.strip()
        if not self.project_name:
            raise ValueError("project_name must not be empty")
        self.max_image_size = max(64, min(32768, self.max_image_size))
        self.micro_max_image_size = max(512, min(65536, self.micro_max_image_size))
        self.compression_level = max(0, min(9, self.compression_level))
        self.pyramid_levels = max(0, min(10, self.pyramid_levels))
        self.tile_size = max(128, min(4096, self.tile_size))
        self.image_quality = max(1, min(100, self.image_quality))

    @classmethod
    def from_dict(cls, data: Any) -> tuple[Config, list[str]]:
        """Build a Config from untrusted data (a JSON file or saved preset).

        Unknown keys are ignored and values of the wrong type fall back to the
        field default, so one bad entry can neither crash the load nor be
        misread (the string ``"false"`` must not become ``True``). Returns the
        config and a list of human-readable problems for the caller to show.
        """
        problems: list[str] = []
        if not isinstance(data, dict):
            return cls(), ["configuration is not a JSON object; defaults used"]
        defaults = cls()
        clean: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            default = getattr(defaults, f.name)
            coerced = _coerce(value, default, f.name)
            if coerced is _INVALID:
                problems.append(f"ignored invalid value for '{f.name}'")
            else:
                clean[f.name] = coerced
        unknown = sorted(str(k) for k in data if k not in cls.__dataclass_fields__)
        if unknown:
            problems.append("ignored unknown keys: " + ", ".join(unknown))
        try:
            return cls(**clean), problems
        except (TypeError, ValueError) as exc:
            clean.pop("project_name", None)
            problems.append(f"project name rejected ({exc})")
            return cls(**clean), problems


_INVALID = object()
_TRUE = {"true", "yes", "1", "on"}
_FALSE = {"false", "no", "0", "off"}


def _coerce(value: Any, default: Any, name: str) -> Any:
    """Coerce *value* to the type of *default*, or return ``_INVALID``."""
    if name == "reference_slide":
        if value is None or isinstance(value, str):
            return value
        return _INVALID
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in _TRUE | _FALSE:
            return value.strip().lower() in _TRUE
        return _INVALID
    if isinstance(default, int):
        if isinstance(value, bool):
            return _INVALID
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                return _INVALID
        return _INVALID
    if isinstance(default, str):
        return value if isinstance(value, str) else _INVALID
    return _INVALID
