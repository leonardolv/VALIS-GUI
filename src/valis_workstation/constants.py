"""Configuration key constants to avoid hardcoded strings."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class ConfigKeys(StrEnum):
    """Central registry of configuration keys.

    Using constants prevents typos and makes refactoring easier.
    """

    # Basic registration settings
    PROJECT_NAME = "project_name"
    RIGID_REGISTRATION = "rigid_registration"
    NON_RIGID_REGISTRATION = "non_rigid_registration"
    MAX_IMAGE_SIZE = "max_image_size"
    USE_GPU = "use_gpu"

    # Advanced settings
    FEATURE_DETECTOR = "feature_detector"
    TRANSFORMER_TYPE = "transformer_type"
    REFERENCE_SLIDE = "reference_slide"
    CROP_MODE = "crop_mode"
    USE_MASKS = "use_masks"
    DENOISE = "denoise"
    IMGS_ORDERED = "imgs_ordered"

    # Micro-registration
    MICRO_REGISTRATION = "micro_registration"
    MICRO_MAX_IMAGE_SIZE = "micro_max_image_size"

    # Save options
    COMPRESSION_LEVEL = "compression_level"
    PYRAMID_LEVELS = "pyramid_levels"
    TILE_SIZE = "tile_size"
    IMAGE_QUALITY = "image_quality"
    IMAGE_FORMAT = "image_format"

    # QSettings keys for persistence
    WINDOW_GEOMETRY = "geometry"
    WINDOW_STATE = "windowState"
    RECENT_FOLDERS = "recent_folders"
    LAST_PROJECT_DIR = "last_project_dir"
    LAST_CONFIG_DIR = "last_config_dir"

    @classmethod
    def all(cls) -> list[str]:
        return [member.value for member in cls]


class FeatureDetectors(StrEnum):
    """Available feature detector algorithms.

    Only detectors that have a corresponding class in
    ``valis.feature_detectors`` are listed.  SIFT is **not** provided by
    VALIS; DeDoDe is available through Kornia.
    """

    VGG = "vgg"
    KAZE = "kaze"
    BRISK = "brisk"
    ORB = "orb"
    AKAZE = "akaze"
    SUPERPOINT = "superpoint"
    DISK = "disk"
    DEDODE = "dedode"

    @property
    def label(self) -> str:
        labels: dict[FeatureDetectors, str] = {
            FeatureDetectors.VGG: "VGG (default - BRISK detect + VGG descriptor)",
            FeatureDetectors.KAZE: "KAZE (scale-space, good for textured tissue)",
            FeatureDetectors.BRISK: "BRISK (fast binary descriptor)",
            FeatureDetectors.ORB: "ORB (fast, rotation-invariant)",
            FeatureDetectors.AKAZE: "AKAZE (accelerated KAZE)",
            FeatureDetectors.SUPERPOINT: "SuperPoint (deep learning, needs GPU)",
            FeatureDetectors.DISK: "DISK (deep learning, needs GPU)",
            FeatureDetectors.DEDODE: "DeDoDe (deep learning, needs GPU)",
        }
        return labels[self]

    @classmethod
    def all(cls) -> list[str]:
        """Get all available detector keys."""
        return [member.value for member in cls]

    @classmethod
    def label_for(cls, key: str | FeatureDetectors) -> str:
        """Return the human-readable label for *key*."""
        try:
            return cls(key).label
        except ValueError:
            return str(key)

    @classmethod
    def key_for_label(cls, label: str) -> str:
        """Return the detector key for a human-readable *label*."""
        for member in cls:
            if member.label == label:
                return member.value
        return label  # fallback: the label *is* the key


class TransformerTypes(StrEnum):
    """Rigid transformation models passed as ``transformer_cls``.

    These control the *rigid* alignment model only.  Non-rigid warping is
    controlled separately by the non-rigid registration checkbox.
    """

    SIMILARITY = "similarity"
    AFFINE = "affine"
    RIGID = "rigid"

    @property
    def label(self) -> str:
        labels: dict[TransformerTypes, str] = {
            TransformerTypes.SIMILARITY: "Similarity (rotation + scale + translation, default)",
            TransformerTypes.AFFINE: "Affine (rotation + scale + shear + translation)",
            TransformerTypes.RIGID: "Rigid / Euclidean (rotation + translation only)",
        }
        return labels[self]

    @classmethod
    def all(cls) -> list[str]:
        """Get all transformer type keys."""
        return [member.value for member in cls]

    @classmethod
    def label_for(cls, key: str | TransformerTypes) -> str:
        try:
            return cls(key).label
        except ValueError:
            return str(key)

    @classmethod
    def key_for_label(cls, label: str) -> str:
        for member in cls:
            if member.label == label:
                return member.value
        return label


class CropModes(StrEnum):
    """Available crop modes for registered images."""

    REFERENCE = "reference"
    ALL_OVERLAP = "all_overlap"
    ALL = "all"
    UNCHANGED = "unchanged"

    @classmethod
    def all(cls) -> list[str]:
        """Get all crop modes."""
        return [member.value for member in cls]


class NonRigidMethods(StrEnum):
    """Non-rigid registration methods."""

    OPTICAL_FLOW = "optical_flow"
    RAFT = "raft"

    @property
    def label(self) -> str:
        labels: dict[NonRigidMethods, str] = {
            NonRigidMethods.OPTICAL_FLOW: "Optical Flow (default)",
            NonRigidMethods.RAFT: "RAFT (deep learning, VALIS v1.2.0+)",
        }
        return labels[self]

    @classmethod
    def all(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def label_for(cls, key: str) -> str:
        try:
            return cls(key).label
        except ValueError:
            return str(key)

    @classmethod
    def key_for_label(cls, label: str) -> str:
        for member in cls:
            if member.label == label:
                return member.value
        return label


class ImageFormats(StrEnum):
    """Supported output image formats."""

    OME_TIFF = "OME-TIFF"
    TIFF = "TIFF"
    JPEG = "JPEG"
    PNG = "PNG"

    @classmethod
    def all(cls) -> list[str]:
        """Get all formats."""
        return [member.value for member in cls]


# The TIFF compression *method* names ``pyvips.Image.tiffsave`` (and
# therefore ``valis.slide_io.save_ome_tiff``, which forwards its
# ``compression`` argument straight through and calls ``.lower()`` on it)
# actually accepts. See
# https://libvips.github.io/pyvips/enums.html#pyvips.enums.ForeignTiffCompression
_COMPRESSION_LEVEL_METHODS: tuple[str, ...] = (
    "none",  # 0 - "No compression (fastest, largest)"
    "lzw",  # 1 - "Fast compression (good balance)"
    "lzw",  # 2
    "lzw",  # 3
    "lzw",  # 4
    "deflate",  # 5 - matches VALIS's own DEFAULT_COMPRESSION
    "deflate",  # 6
    "deflate",  # 7
    "deflate",  # 8
    "deflate",  # 9 - "Maximum compression (slowest, smallest)"
)


def compression_level_to_method(level: int) -> str:
    """Map the GUI's 0-9 "compression level" spinbox value to a TIFF
    compression *method name* that VALIS/pyvips will actually accept.

    ``Config.compression_level`` and the Save Options/Properties dock
    spinboxes model a single 0-9 slider, following their own tooltip's
    zlib-style "0 = none ... 9 = maximum" framing. But
    ``Valis.warp_and_save_slides``/``warp_and_merge_slides`` forward
    whatever they're given for ``compression`` straight through to
    ``slide_io.save_ome_tiff``, which immediately calls
    ``compression.lower()`` on it before handing it to
    ``pyvips.Image.tiffsave`` - there is no numeric "level" parameter
    anywhere on this path, only a fixed set of method names (``"none"``,
    ``"lzw"``, ``"deflate"``, ``"jpeg"``, ...). Passing the raw int
    straight through (as both ``services/valis_pipeline.py`` and
    ``services/merge_slides.py`` used to) crashes every real save with
    ``AttributeError: 'int' object has no attribute 'lower'`` - this
    function exists to be called before either kwargs dict reaches VALIS.

    Values outside ``0-9`` are clamped rather than raising, matching
    ``Config.__post_init__``'s own clamping of the same field.
    """
    index = max(0, min(len(_COMPRESSION_LEVEL_METHODS) - 1, int(level)))
    return _COMPRESSION_LEVEL_METHODS[index]


# Shared supported extensions for slide discovery/validation.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".tif",
        ".tiff",
        ".ome.tif",
        ".ome.tiff",
        ".svs",
        ".ndpi",
        ".vsi",
        ".czi",
        ".scn",
        ".png",
        ".jpg",
        ".jpeg",
    }
)


def has_supported_extension(path: str | Path) -> bool:
    """Return ``True`` when *path* matches one of ``SUPPORTED_EXTENSIONS``.

    ``Path.suffix`` cannot detect compound extensions such as ``.ome.tiff``,
    so we normalize and use ``endswith`` checks.
    """
    suffix_target = str(path).lower()
    return any(suffix_target.endswith(ext) for ext in SUPPORTED_EXTENSIONS)
