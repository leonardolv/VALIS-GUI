"""Service for generating thumbnails from whole slide images."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtCore, QtGui

from valis_workstation.services.thumbnail_cache import get_thumbnail_cache
from valis_workstation.utils.performance import get_performance_monitor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def generate_thumbnail(
    slide_path: Path,
    max_size: int = 512,
    reader_type: str | None = None,
    use_cache: bool = True,
) -> tuple[QtGui.QPixmap | None, dict]:
    """Generate a thumbnail from a whole slide image.

    Parameters
    ----------
    slide_path : Path
        Path to the slide file
    max_size : int
        Maximum width or height of the thumbnail in pixels
    reader_type : str | None
        Preferred reader type ("bioformats", "openslide", "pyvips", or None for auto)
    use_cache : bool
        Whether to use cached thumbnails if available (default: True)

    Returns
    -------
    tuple[QtGui.QPixmap | None, dict]
        Tuple of (thumbnail pixmap, metadata dict)
        Returns (None, {}) if thumbnail generation fails
    """
    if not slide_path.exists():
        logger.warning(f"Slide file not found: {slide_path}")
        return None, {}

    started_at = time.time()

    # Try to get from cache first
    if use_cache:
        cache = get_thumbnail_cache()
        cached_result = cache.get(slide_path)
        if cached_result is not None:
            logger.info(f"Using cached thumbnail for: {slide_path.name}")
            get_performance_monitor().track_thumbnail_load(
                time.time() - started_at, from_cache=True
            )
            return cached_result

    logger.info(f"Generating thumbnail for: {slide_path.name}")

    # Try VALIS slide_io first (supports multiple formats)
    try:
        from valis import slide_io

        # Read the slide
        slide_reader = slide_io.get_slide_reader(
            str(slide_path),
            series=None,  # Use default series
        )

        logger.info(f"Using {slide_reader.__class__.__name__} to read slide")

        # Get metadata
        metadata = _extract_metadata(slide_reader, slide_path)

        # Get thumbnail
        # Try to get a built-in thumbnail first (faster)
        thumbnail_array = None

        if hasattr(slide_reader, "slide") and hasattr(
            slide_reader.slide, "associated_images"
        ):
            # OpenSlide-based readers have associated images
            if "thumbnail" in slide_reader.slide.associated_images:
                try:
                    thumbnail_pil = slide_reader.slide.associated_images["thumbnail"]
                    thumbnail_array = np.array(thumbnail_pil)
                    logger.info("Using built-in thumbnail from slide")
                except Exception as e:
                    logger.warning(f"Failed to get built-in thumbnail: {e}")

        # If no built-in thumbnail, generate from lowest resolution level
        if thumbnail_array is None:
            try:
                # Get the lowest resolution level
                n_levels = slide_reader.metadata.n_levels
                lowest_level = n_levels - 1 if n_levels > 1 else 0

                logger.info(
                    f"Generating thumbnail from level {lowest_level}/{n_levels - 1}"
                )

                # Read the lowest level (this should be small)
                thumbnail_array = slide_reader.slide2vips(level=lowest_level)

                # Convert to numpy if needed
                if not isinstance(thumbnail_array, np.ndarray):
                    # pyvips image
                    if hasattr(thumbnail_array, "numpy"):
                        thumbnail_array = thumbnail_array.numpy()
                    else:
                        # Manual conversion
                        thumbnail_array = np.ndarray(
                            buffer=thumbnail_array.write_to_memory(),
                            dtype=np.uint8,
                            shape=[
                                thumbnail_array.height,
                                thumbnail_array.width,
                                thumbnail_array.bands,
                            ],
                        )

            except Exception as e:
                logger.warning(f"Failed to generate thumbnail from level: {e}")
                # Last resort: read a small crop from level 0
                try:
                    width, height = metadata.get("dimensions", (1000, 1000))
                    crop_size = min(width, height, 2048)
                    thumbnail_array = slide_reader.slide2image(
                        level=0, xywh=(0, 0, crop_size, crop_size)
                    )
                except Exception as e2:
                    logger.error(f"Failed to generate thumbnail crop: {e2}")
                    return None, metadata

        # Convert to QPixmap
        if thumbnail_array is not None:
            pixmap = _numpy_to_pixmap(thumbnail_array, max_size)

            # Cache the thumbnail for future use
            if use_cache and pixmap is not None:
                cache = get_thumbnail_cache()
                cache.put(slide_path, pixmap, metadata)

            get_performance_monitor().track_thumbnail_load(
                time.time() - started_at, from_cache=False
            )
            return pixmap, metadata

    except ImportError:
        logger.warning("VALIS not available, cannot generate thumbnails")
    except Exception as e:
        logger.exception(f"Failed to generate thumbnail: {e}")

    return None, {}


def _extract_metadata(slide_reader, slide_path: Path) -> dict:
    """Extract metadata from slide reader.

    Parameters
    ----------
    slide_reader
        VALIS slide reader object
    slide_path : Path
        Path to the slide file

    Returns
    -------
    dict
        Metadata dictionary with dimensions, dtype, channels, etc.
    """
    metadata = {
        "file_path": str(slide_path),
    }

    try:
        if hasattr(slide_reader, "metadata"):
            meta = slide_reader.metadata

            # Dimensions (level 0)
            if hasattr(meta, "slide_dimensions"):
                width, height = meta.slide_dimensions
                metadata["dimensions"] = (width, height)
            elif hasattr(meta, "level_dimensions") and meta.level_dimensions:
                width, height = meta.level_dimensions[0]
                metadata["dimensions"] = (width, height)

            # Number of channels
            if hasattr(meta, "n_channels"):
                metadata["channels"] = meta.n_channels
            elif hasattr(meta, "is_rgb"):
                metadata["channels"] = 3 if meta.is_rgb else 1

            # Pixel type
            if hasattr(meta, "bf_datatype"):
                metadata["dtype"] = str(meta.bf_datatype)

            # Series (for multi-series files)
            if hasattr(meta, "n_series") and meta.n_series > 1:
                metadata["series"] = meta.n_series

    except Exception as e:
        logger.warning(f"Failed to extract some metadata: {e}")

    return metadata


def _numpy_to_pixmap(array: np.ndarray, max_size: int) -> QtGui.QPixmap:
    """Convert numpy array to QPixmap and scale to max size.

    Parameters
    ----------
    array : np.ndarray
        Image array (H, W) or (H, W, C)
    max_size : int
        Maximum width or height

    Returns
    -------
    QtGui.QPixmap
        Scaled pixmap
    """
    # Ensure uint8
    if array.dtype != np.uint8:
        # Scale to 0-255
        if array.max() > 255:
            array = ((array - array.min()) / (array.max() - array.min()) * 255).astype(
                np.uint8
            )
        else:
            array = array.astype(np.uint8)

    # Handle different image formats
    if array.ndim == 2:
        # Grayscale
        height, width = array.shape
        bytes_per_line = width
        qimage = QtGui.QImage(
            array.data, width, height, bytes_per_line, QtGui.QImage.Format_Grayscale8
        )
    elif array.ndim == 3:
        height, width, channels = array.shape

        if channels == 1:
            # Grayscale with channel dimension
            array = array.squeeze(2)
            qimage = QtGui.QImage(
                array.data, width, height, width, QtGui.QImage.Format_Grayscale8
            )
        elif channels == 3:
            # RGB
            bytes_per_line = width * 3
            qimage = QtGui.QImage(
                array.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
            )
        elif channels == 4:
            # RGBA
            bytes_per_line = width * 4
            qimage = QtGui.QImage(
                array.data, width, height, bytes_per_line, QtGui.QImage.Format_RGBA8888
            )
        else:
            # Multi-channel, use first 3 channels as RGB
            logger.warning(
                f"Multi-channel image ({channels} channels), using first 3 as RGB"
            )
            array = array[:, :, :3]
            bytes_per_line = width * 3
            qimage = QtGui.QImage(
                array.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
            )
    else:
        logger.error(f"Unexpected array shape: {array.shape}")
        # Create a placeholder
        qimage = QtGui.QImage(128, 128, QtGui.QImage.Format_RGB888)
        qimage.fill(QtGui.QColor(200, 200, 200))

    # Convert to pixmap and scale
    pixmap = QtGui.QPixmap.fromImage(qimage.copy())

    # Scale to max size while maintaining aspect ratio
    if pixmap.width() > max_size or pixmap.height() > max_size:
        pixmap = pixmap.scaled(
            max_size,
            max_size,
            aspectMode=QtCore.Qt.KeepAspectRatio,
            mode=QtCore.Qt.SmoothTransformation,
        )

    return pixmap
