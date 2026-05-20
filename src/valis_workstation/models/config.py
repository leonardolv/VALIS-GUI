from __future__ import annotations

from dataclasses import dataclass, field


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
    compression_level: int = 1  # 0 – 9
    pyramid_levels: int = 4
    tile_size: int = 512
    image_quality: int = 95  # JPEG quality 1 – 100
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
