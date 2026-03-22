from __future__ import annotations

from dataclasses import dataclass


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

    # Micro-registration settings
    micro_registration: bool = False
    micro_max_image_size: int = 4096

    # ── Output / save settings ──────────────────────────────────────
    compression_level: int = 1  # 0 – 9
    pyramid_levels: int = 4
    tile_size: int = 512
    image_quality: int = 95  # JPEG quality 1 – 100
