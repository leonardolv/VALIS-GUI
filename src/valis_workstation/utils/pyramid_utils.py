"""
Pyramid level selection utilities for optimal image display.

This module provides functions to automatically select the best pyramid level
for displaying whole slide images based on viewport size and zoom level, avoiding
unnecessary memory usage from loading full-resolution images.

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import logging
import math
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def calculate_optimal_level(
    image_dimensions: Tuple[int, int],
    viewport_size: Tuple[int, int],
    zoom_factor: float = 1.0,
    pyramid_levels: Optional[int] = None,
    level_downsamples: Optional[list[float]] = None,
) -> int:
    """
    Calculate the optimal pyramid level for displaying an image.
    
    The algorithm selects the lowest resolution level that still provides
    sufficient detail for the current viewport and zoom level. This minimizes
    memory usage while maintaining visual quality.
    
    Parameters
    ----------
    image_dimensions : Tuple[int, int]
        Full resolution image dimensions (width, height) at level 0
    viewport_size : Tuple[int, int]
        Size of the display viewport (width, height) in pixels
    zoom_factor : float
        Current zoom factor (1.0 = 100%, 2.0 = 200%, etc.)
    pyramid_levels : Optional[int]
        Total number of pyramid levels available
    level_downsamples : Optional[list[float]]
        Downsample factors for each level (e.g., [1.0, 2.0, 4.0, 8.0])
        
    Returns
    -------
    int
        Optimal pyramid level index (0 = highest resolution)
        
    Notes
    -----
    The algorithm works as follows:
    1. Calculate required resolution = viewport_size * zoom_factor
    2. Find the lowest level where image_size >= required resolution
    3. Add safety margin to avoid undersampling artifacts
    
    Examples
    --------
    >>> # Image: 40000x30000, Viewport: 1000x800, Zoom: 1.0
    >>> calculate_optimal_level((40000, 30000), (1000, 800), 1.0)
    4  # Uses ~2500x1875 resolution (downsample ~16x)
    
    >>> # Same image, zoomed in 4x
    >>> calculate_optimal_level((40000, 30000), (1000, 800), 4.0)
    2  # Uses ~10000x7500 resolution (downsample ~4x)
    """
    img_width, img_height = image_dimensions
    view_width, view_height = viewport_size
    
    # Calculate required resolution (viewport * zoom + safety margin)
    # Safety margin of 1.5x to ensure we don't undersample
    safety_margin = 1.5
    required_width = view_width * zoom_factor * safety_margin
    required_height = view_height * zoom_factor * safety_margin
    
    logger.debug(
        f"Image: {img_width}x{img_height}, "
        f"Viewport: {view_width}x{view_height}, "
        f"Zoom: {zoom_factor}x, "
        f"Required: {required_width:.0f}x{required_height:.0f}"
    )
    
    # If we have explicit downsample factors, use them
    if level_downsamples is not None:
        for level, downsample in enumerate(level_downsamples):
            level_width = img_width / downsample
            level_height = img_height / downsample
            
            # Check if this level provides sufficient resolution
            if level_width >= required_width and level_height >= required_height:
                logger.debug(
                    f"Selected level {level} (downsample {downsample}x, "
                    f"resolution {level_width:.0f}x{level_height:.0f})"
                )
                return level
        
        # If no level is sufficient, use highest resolution
        logger.debug("No level sufficient, using level 0 (full resolution)")
        return 0
    
    # Otherwise, calculate based on number of levels
    if pyramid_levels is None:
        # Estimate number of levels from image dimensions
        # Typical pyramid stops when smaller dimension < 256 pixels
        min_dim = min(img_width, img_height)
        pyramid_levels = max(1, int(math.log2(min_dim / 256)) + 1)
        logger.debug(f"Estimated {pyramid_levels} pyramid levels")
    
    # Calculate downsample factor needed
    width_downsample = img_width / required_width
    height_downsample = img_height / required_height
    required_downsample = min(width_downsample, height_downsample)
    
    # Clamp to reasonable range
    required_downsample = max(1.0, required_downsample)
    
    # Convert downsample to level (assuming power-of-2 pyramid)
    # Level 0: downsample=1, Level 1: downsample=2, Level 2: downsample=4, etc.
    optimal_level = int(math.log2(required_downsample))
    
    # Clamp to available levels
    optimal_level = max(0, min(optimal_level, pyramid_levels - 1))
    
    actual_downsample = 2 ** optimal_level
    actual_width = img_width / actual_downsample
    actual_height = img_height / actual_downsample
    
    logger.debug(
        f"Selected level {optimal_level} (downsample {actual_downsample}x, "
        f"resolution {actual_width:.0f}x{actual_height:.0f})"
    )
    
    return optimal_level


def get_level_dimensions(
    base_dimensions: Tuple[int, int],
    level: int,
    downsample: Optional[float] = None,
) -> Tuple[int, int]:
    """
    Calculate the dimensions of an image at a specific pyramid level.
    
    Parameters
    ----------
    base_dimensions : Tuple[int, int]
        Dimensions at level 0 (width, height)
    level : int
        Pyramid level index
    downsample : Optional[float]
        Explicit downsample factor for this level.
        If None, assumes power-of-2 pyramid (2^level)
        
    Returns
    -------
    Tuple[int, int]
        Dimensions at the specified level (width, height)
    """
    if downsample is None:
        downsample = 2 ** level
    
    width = int(base_dimensions[0] / downsample)
    height = int(base_dimensions[1] / downsample)
    
    return (width, height)


def estimate_memory_usage(
    dimensions: Tuple[int, int],
    bytes_per_pixel: int = 3,
) -> float:
    """
    Estimate memory usage for loading an image of given dimensions.
    
    Parameters
    ----------
    dimensions : Tuple[int, int]
        Image dimensions (width, height)
    bytes_per_pixel : int
        Bytes per pixel (3 for RGB, 1 for grayscale, 4 for RGBA)
        
    Returns
    -------
    float
        Estimated memory usage in megabytes
    """
    width, height = dimensions
    total_pixels = width * height
    total_bytes = total_pixels * bytes_per_pixel
    total_mb = total_bytes / (1024 * 1024)
    
    return total_mb


def should_use_tiles(
    dimensions: Tuple[int, int],
    memory_limit_mb: float = 512.0,
    bytes_per_pixel: int = 3,
) -> bool:
    """
    Determine if tile-based loading should be used for an image.
    
    Parameters
    ----------
    dimensions : Tuple[int, int]
        Image dimensions (width, height)
    memory_limit_mb : float
        Memory limit in megabytes for non-tiled loading
    bytes_per_pixel : int
        Bytes per pixel
        
    Returns
    -------
    bool
        True if tile-based loading should be used
    """
    estimated_mb = estimate_memory_usage(dimensions, bytes_per_pixel)
    
    if estimated_mb > memory_limit_mb:
        logger.info(
            f"Image {dimensions[0]}x{dimensions[1]} requires {estimated_mb:.1f}MB "
            f"(exceeds limit of {memory_limit_mb}MB), using tile-based loading"
        )
        return True
    
    return False


class PyramidLevelSelector:
    """
    Helper class for managing pyramid level selection with caching.
    
    This class maintains state about the current viewport, zoom level, and
    selected pyramid level, recalculating only when necessary.
    """
    
    def __init__(
        self,
        image_dimensions: Tuple[int, int],
        pyramid_levels: Optional[int] = None,
        level_downsamples: Optional[list[float]] = None,
    ):
        """
        Initialize the pyramid level selector.
        
        Parameters
        ----------
        image_dimensions : Tuple[int, int]
            Full resolution image dimensions (width, height)
        pyramid_levels : Optional[int]
            Number of pyramid levels
        level_downsamples : Optional[list[float]]
            Downsample factor for each level
        """
        self.image_dimensions = image_dimensions
        self.pyramid_levels = pyramid_levels
        self.level_downsamples = level_downsamples
        
        # Cache current state
        self._current_viewport: Optional[Tuple[int, int]] = None
        self._current_zoom: float = 1.0
        self._current_level: int = 0
    
    def update(
        self,
        viewport_size: Tuple[int, int],
        zoom_factor: float = 1.0,
    ) -> Tuple[int, bool]:
        """
        Update viewport/zoom and recalculate optimal level if needed.
        
        Parameters
        ----------
        viewport_size : Tuple[int, int]
            Current viewport size (width, height)
        zoom_factor : float
            Current zoom factor
            
        Returns
        -------
        Tuple[int, bool]
            (optimal_level, level_changed)
            - optimal_level: The selected pyramid level
            - level_changed: True if level changed from previous call
        """
        # Check if recalculation is needed
        needs_update = (
            self._current_viewport != viewport_size or
            abs(self._current_zoom - zoom_factor) > 0.1  # 10% change threshold
        )
        
        if not needs_update:
            return self._current_level, False
        
        # Calculate new optimal level
        new_level = calculate_optimal_level(
            self.image_dimensions,
            viewport_size,
            zoom_factor,
            self.pyramid_levels,
            self.level_downsamples,
        )
        
        # Update cache
        level_changed = new_level != self._current_level
        self._current_viewport = viewport_size
        self._current_zoom = zoom_factor
        self._current_level = new_level
        
        if level_changed:
            logger.info(
                f"Pyramid level changed: {self._current_level} → {new_level} "
                f"(zoom: {zoom_factor:.2f}x)"
            )
        
        return new_level, level_changed
    
    def get_current_level(self) -> int:
        """Get the currently selected pyramid level."""
        return self._current_level
    
    def get_current_dimensions(self) -> Tuple[int, int]:
        """Get dimensions at the currently selected level."""
        if self.level_downsamples is not None:
            downsample = self.level_downsamples[self._current_level]
        else:
            downsample = None
        
        return get_level_dimensions(
            self.image_dimensions,
            self._current_level,
            downsample,
        )
