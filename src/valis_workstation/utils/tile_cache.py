"""
Tile-based lazy loading system for memory-efficient image display.

This module implements a tile caching system with LRU eviction for displaying
very large whole slide images without loading the entire image into memory.

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import logging
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict
import threading

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TileKey:
    """
    Unique identifier for a tile.
    
    Attributes
    ----------
    slide_path : str
        Path to the slide file
    level : int
        Pyramid level
    tile_x : int
        Tile X coordinate
    tile_y : int
        Tile Y coordinate
    """
    slide_path: str
    level: int
    tile_x: int
    tile_y: int
    
    def __hash__(self):
        return hash((self.slide_path, self.level, self.tile_x, self.tile_y))


class LRUTileCache:
    """
    LRU (Least Recently Used) cache for image tiles.
    
    This cache stores tiles in memory up to a configurable limit, evicting
    the least recently accessed tiles when the limit is exceeded.
    
    Thread-safe implementation using locks.
    """
    
    def __init__(self, max_memory_mb: float = 1024.0, tile_size: int = 512):
        """
        Initialize the LRU tile cache.
        
        Parameters
        ----------
        max_memory_mb : float
            Maximum memory usage in megabytes (default: 1GB)
        tile_size : int
            Default tile size in pixels (default: 512x512)
        """
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.tile_size = tile_size
        
        # OrderedDict maintains insertion order, making LRU easy
        self._cache: OrderedDict[TileKey, np.ndarray] = OrderedDict()
        self._memory_usage = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(
            f"Initialized LRU tile cache: {max_memory_mb}MB limit, "
            f"{tile_size}x{tile_size} tiles"
        )
    
    def get(self, key: TileKey) -> Optional[np.ndarray]:
        """
        Retrieve a tile from the cache.
        
        Parameters
        ----------
        key : TileKey
            Tile identifier
            
        Returns
        -------
        Optional[np.ndarray]
            Tile data if in cache, None otherwise
        """
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug(f"Cache hit: {key.slide_path} L{key.level} ({key.tile_x}, {key.tile_y})")
                return self._cache[key]
            else:
                self._misses += 1
                logger.debug(f"Cache miss: {key.slide_path} L{key.level} ({key.tile_x}, {key.tile_y})")
                return None
    
    def put(self, key: TileKey, tile_data: np.ndarray) -> None:
        """
        Store a tile in the cache.
        
        Parameters
        ----------
        key : TileKey
            Tile identifier
        tile_data : np.ndarray
            Tile image data
        """
        with self._lock:
            # Calculate tile size
            tile_bytes = tile_data.nbytes
            
            # If tile is already cached, remove old entry
            if key in self._cache:
                old_data = self._cache[key]
                self._memory_usage -= old_data.nbytes
                del self._cache[key]
            
            # Evict tiles if necessary
            while self._memory_usage + tile_bytes > self.max_memory_bytes and self._cache:
                # Remove least recently used (first item)
                old_key, old_data = self._cache.popitem(last=False)
                self._memory_usage -= old_data.nbytes
                self._evictions += 1
                logger.debug(
                    f"Evicted tile: {old_key.slide_path} L{old_key.level} "
                    f"({old_key.tile_x}, {old_key.tile_y})"
                )
            
            # Add new tile
            self._cache[key] = tile_data
            self._memory_usage += tile_bytes
            
            logger.debug(
                f"Cached tile: {key.slide_path} L{key.level} ({key.tile_x}, {key.tile_y}) "
                f"[{tile_bytes / (1024*1024):.2f}MB, total: {self._memory_usage / (1024*1024):.2f}MB]"
            )
    
    def clear(self) -> None:
        """Clear all cached tiles."""
        with self._lock:
            self._cache.clear()
            self._memory_usage = 0
            logger.info("Cleared tile cache")
    
    def clear_slide(self, slide_path: str) -> None:
        """
        Clear all tiles for a specific slide.
        
        Parameters
        ----------
        slide_path : str
            Path to the slide file
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.slide_path == slide_path
            ]
            
            for key in keys_to_remove:
                tile_data = self._cache[key]
                self._memory_usage -= tile_data.nbytes
                del self._cache[key]
            
            logger.info(f"Cleared {len(keys_to_remove)} tiles for {slide_path}")
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns
        -------
        Dict
            Statistics dictionary with hits, misses, memory usage, etc.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'tile_count': len(self._cache),
                'memory_usage_mb': self._memory_usage / (1024 * 1024),
                'memory_limit_mb': self.max_memory_bytes / (1024 * 1024),
                'memory_usage_pct': (self._memory_usage / self.max_memory_bytes) * 100,
            }
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0


class TiledImageLoader:
    """
    Tile-based image loader for whole slide images.
    
    This class handles loading image tiles on demand, using VALIS slide readers
    and an LRU cache for memory efficiency.
    """
    
    def __init__(
        self,
        slide_path: Path,
        tile_size: int = 512,
        cache: Optional[LRUTileCache] = None,
    ):
        """
        Initialize the tiled image loader.
        
        Parameters
        ----------
        slide_path : Path
            Path to the slide file
        tile_size : int
            Size of tiles in pixels (default: 512x512)
        cache : Optional[LRUTileCache]
            Tile cache to use. If None, creates a new cache.
        """
        self.slide_path = slide_path
        self.tile_size = tile_size
        
        # Use provided cache or create new one
        self.cache = cache if cache is not None else LRUTileCache(tile_size=tile_size)
        
        # Initialize slide reader (lazy loading)
        self._reader = None
        self._reader_lock = threading.Lock()
        
        logger.info(f"Initialized tiled loader for: {slide_path.name}")
    
    def _get_reader(self):
        """Get slide reader (lazy initialization)."""
        if self._reader is None:
            with self._reader_lock:
                if self._reader is None:  # Double-check after acquiring lock
                    from valis import slide_io
                    self._reader = slide_io.get_slide_reader(str(self.slide_path))
                    logger.info(f"Initialized slide reader: {self._reader.__class__.__name__}")
        
        return self._reader
    
    def get_tile(
        self,
        tile_x: int,
        tile_y: int,
        level: int = 0,
    ) -> Optional[np.ndarray]:
        """
        Load a tile from the slide.
        
        Parameters
        ----------
        tile_x : int
            Tile X coordinate (in tile units, not pixels)
        tile_y : int
            Tile Y coordinate (in tile units, not pixels)
        level : int
            Pyramid level to load from
            
        Returns
        -------
        Optional[np.ndarray]
            Tile data as numpy array, or None if loading fails
        """
        # Create cache key
        key = TileKey(
            slide_path=str(self.slide_path),
            level=level,
            tile_x=tile_x,
            tile_y=tile_y,
        )
        
        # Check cache first
        cached_tile = self.cache.get(key)
        if cached_tile is not None:
            return cached_tile
        
        # Load from slide
        try:
            reader = self._get_reader()
            
            # Calculate pixel coordinates
            pixel_x = tile_x * self.tile_size
            pixel_y = tile_y * self.tile_size
            
            # Get image dimensions at this level
            if hasattr(reader, 'metadata') and hasattr(reader.metadata, 'level_dimensions'):
                level_dims = reader.metadata.level_dimensions[level]
            else:
                # Fallback: use level 0 dimensions with downsample
                base_dims = (reader.metadata.slide_dimensions[0], reader.metadata.slide_dimensions[1])
                downsample = 2 ** level
                level_dims = (base_dims[0] // downsample, base_dims[1] // downsample)
            
            # Clamp to image bounds
            max_x = min(pixel_x + self.tile_size, level_dims[0])
            max_y = min(pixel_y + self.tile_size, level_dims[1])
            
            if pixel_x >= level_dims[0] or pixel_y >= level_dims[1]:
                # Tile is completely outside image bounds
                logger.debug(f"Tile ({tile_x}, {tile_y}) outside bounds at level {level}")
                return None
            
            # Calculate actual tile size
            actual_width = max_x - pixel_x
            actual_height = max_y - pixel_y
            
            # Read tile from slide
            # Note: Different readers have different APIs
            if hasattr(reader.slide, 'read_region'):
                # OpenSlide-based reader
                tile_pil = reader.slide.read_region(
                    (pixel_x, pixel_y),
                    level,
                    (actual_width, actual_height)
                )
                tile_data = np.array(tile_pil)
                # OpenSlide returns RGBA, convert to RGB if needed
                if tile_data.shape[2] == 4:
                    tile_data = tile_data[:, :, :3]
            else:
                # Generic reader - use VALIS API
                tile_data = reader.slide2vips(
                    level=level,
                    xywh=(pixel_x, pixel_y, actual_width, actual_height),
                )
            
            # Pad to full tile size if needed (edge tiles)
            if actual_width < self.tile_size or actual_height < self.tile_size:
                padded = np.zeros((self.tile_size, self.tile_size, tile_data.shape[2]), dtype=tile_data.dtype)
                padded[:actual_height, :actual_width] = tile_data
                tile_data = padded
            
            # Cache the tile
            self.cache.put(key, tile_data)
            
            return tile_data
            
        except Exception as e:
            logger.error(f"Failed to load tile ({tile_x}, {tile_y}) at level {level}: {e}")
            return None
    
    def get_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        level: int = 0,
    ) -> Optional[np.ndarray]:
        """
        Load a region composed of multiple tiles.
        
        Parameters
        ----------
        x : int
            X coordinate in pixels
        y : int
            Y coordinate in pixels
        width : int
            Region width in pixels
        height : int
            Region height in pixels
        level : int
            Pyramid level
            
        Returns
        -------
        Optional[np.ndarray]
            Region data as numpy array
        """
        # Calculate tile range
        start_tile_x = x // self.tile_size
        start_tile_y = y // self.tile_size
        end_tile_x = (x + width - 1) // self.tile_size + 1
        end_tile_y = (y + height - 1) // self.tile_size + 1
        
        # Load all required tiles
        tiles = []
        for ty in range(start_tile_y, end_tile_y):
            row_tiles = []
            for tx in range(start_tile_x, end_tile_x):
                tile = self.get_tile(tx, ty, level)
                if tile is None:
                    # Create blank tile if loading fails
                    tile = np.zeros((self.tile_size, self.tile_size, 3), dtype=np.uint8)
                row_tiles.append(tile)
            
            # Concatenate row
            if row_tiles:
                row = np.concatenate(row_tiles, axis=1)
                tiles.append(row)
        
        if not tiles:
            return None
        
        # Concatenate all rows
        full_region = np.concatenate(tiles, axis=0)
        
        # Crop to exact region
        offset_x = x - start_tile_x * self.tile_size
        offset_y = y - start_tile_y * self.tile_size
        
        region = full_region[
            offset_y:offset_y + height,
            offset_x:offset_x + width
        ]
        
        return region
    
    def close(self) -> None:
        """Close the slide reader."""
        if self._reader is not None:
            # Clear tiles for this slide from cache
            self.cache.clear_slide(str(self.slide_path))
            # Note: VALIS readers don't have explicit close method
            self._reader = None
            logger.info(f"Closed tiled loader for: {self.slide_path.name}")


# Global tile cache instance
_global_tile_cache: Optional[LRUTileCache] = None


def get_tile_cache(max_memory_mb: float = 1024.0, tile_size: int = 512) -> LRUTileCache:
    """
    Get the global tile cache instance.
    
    Parameters
    ----------
    max_memory_mb : float
        Maximum memory for cache (only used on first call)
    tile_size : int
        Tile size (only used on first call)
        
    Returns
    -------
    LRUTileCache
        Global tile cache instance
    """
    global _global_tile_cache
    
    if _global_tile_cache is None:
        _global_tile_cache = LRUTileCache(max_memory_mb, tile_size)
    
    return _global_tile_cache
