"""Configuration key constants to avoid hardcoded strings."""

from __future__ import annotations


class ConfigKeys:
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


class FeatureDetectors:
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

    # Human-readable labels shown in the GUI combo box
    LABELS: dict[str, str] = {
        VGG: "VGG (default – BRISK detect + VGG descriptor)",
        KAZE: "KAZE (scale-space, good for textured tissue)",
        BRISK: "BRISK (fast binary descriptor)",
        ORB: "ORB (fast, rotation-invariant)",
        AKAZE: "AKAZE (accelerated KAZE)",
        SUPERPOINT: "SuperPoint (deep learning, needs GPU)",
        DISK: "DISK (deep learning, needs GPU)",
        DEDODE: "DeDoDe (deep learning, needs GPU)",
    }

    @classmethod
    def all(cls) -> list[str]:
        """Get all available detector keys."""
        return [cls.VGG, cls.KAZE, cls.BRISK, cls.ORB,
                cls.AKAZE, cls.SUPERPOINT, cls.DISK, cls.DEDODE]

    @classmethod
    def label_for(cls, key: str) -> str:
        """Return the human-readable label for *key*."""
        return cls.LABELS.get(key, key)

    @classmethod
    def key_for_label(cls, label: str) -> str:
        """Return the detector key for a human-readable *label*."""
        for k, v in cls.LABELS.items():
            if v == label:
                return k
        return label  # fallback: the label *is* the key


class TransformerTypes:
    """Rigid transformation models passed as ``transformer_cls``.

    These control the *rigid* alignment model only.  Non-rigid warping is
    controlled separately by the non-rigid registration checkbox.
    """

    SIMILARITY = "similarity"
    AFFINE = "affine"
    RIGID = "rigid"

    LABELS: dict[str, str] = {
        SIMILARITY: "Similarity (rotation + scale + translation, default)",
        AFFINE: "Affine (rotation + scale + shear + translation)",
        RIGID: "Rigid / Euclidean (rotation + translation only)",
    }

    @classmethod
    def all(cls) -> list[str]:
        """Get all transformer type keys."""
        return [cls.SIMILARITY, cls.AFFINE, cls.RIGID]

    @classmethod
    def label_for(cls, key: str) -> str:
        return cls.LABELS.get(key, key)

    @classmethod
    def key_for_label(cls, label: str) -> str:
        for k, v in cls.LABELS.items():
            if v == label:
                return k
        return label


class CropModes:
    """Available crop modes for registered images."""
    
    REFERENCE = "reference"
    ALL_OVERLAP = "all_overlap"
    ALL = "all"
    UNCHANGED = "unchanged"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all crop modes."""
        return [cls.REFERENCE, cls.ALL_OVERLAP, cls.ALL, cls.UNCHANGED]


class ImageFormats:
    """Supported output image formats."""
    
    OME_TIFF = "OME-TIFF"
    TIFF = "TIFF"
    JPEG = "JPEG"
    PNG = "PNG"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all formats."""
        return [cls.OME_TIFF, cls.TIFF, cls.JPEG, cls.PNG]
