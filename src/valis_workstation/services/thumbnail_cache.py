"""
Thumbnail caching system for VALIS Workstation.

This module provides persistent disk-based caching of slide thumbnails to avoid
regenerating them on every application launch. Cache keys are based on file path
and modification time to automatically invalidate stale cache entries.

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ThumbnailCache:
    """
    Persistent disk-based cache for slide thumbnails.

    The cache stores thumbnails as PNG files with metadata in JSON sidecar files.
    Cache entries are automatically invalidated when the source file is modified.

    Cache Structure:
        .valis_cache/
            thumbnails/
                <hash>.png       - Cached thumbnail image
                <hash>.json      - Metadata (path, mtime, dimensions, etc.)

    The hash is computed from the absolute file path to ensure unique cache keys.
    Modification time (mtime) is stored in metadata to detect file changes.
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_cache_size_mb: int = 500):
        """
        Initialize the thumbnail cache.

        Args:
            cache_dir: Directory for cache storage. If None, uses .valis_cache in user's home
            max_cache_size_mb: Maximum cache size in megabytes (default: 500MB)
        """
        if cache_dir is None:
            # Use user's home directory for cache
            cache_dir = Path.home() / ".valis_cache"

        self.cache_dir = Path(cache_dir) / "thumbnails"
        self.max_cache_size_mb = max_cache_size_mb

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Thumbnail cache initialized at: {self.cache_dir}")
        logger.info(f"Max cache size: {max_cache_size_mb}MB")

    def _get_cache_key(self, slide_path: Path) -> str:
        """
        Generate a cache key from the slide file path.

        Args:
            slide_path: Path to the slide file

        Returns:
            MD5 hash of the absolute file path
        """
        # Use absolute path to ensure consistency
        abs_path = str(slide_path.absolute())

        # Generate MD5 hash
        hash_obj = hashlib.md5(abs_path.encode("utf-8"))
        return hash_obj.hexdigest()

    def _get_cache_paths(self, cache_key: str) -> Tuple[Path, Path]:
        """
        Get the cache file paths for a given cache key.

        Args:
            cache_key: Cache key (MD5 hash)

        Returns:
            Tuple of (image_path, metadata_path)
        """
        image_path = self.cache_dir / f"{cache_key}.png"
        metadata_path = self.cache_dir / f"{cache_key}.json"
        return image_path, metadata_path

    def get(self, slide_path: Path) -> Optional[Tuple[QPixmap, Dict]]:
        """
        Retrieve a cached thumbnail if available and valid.

        Args:
            slide_path: Path to the slide file

        Returns:
            Tuple of (QPixmap, metadata_dict) if cache hit and valid, None otherwise
        """
        try:
            # Check if file exists
            if not slide_path.exists():
                logger.warning(f"Slide file does not exist: {slide_path}")
                return None

            # Get cache key and paths
            cache_key = self._get_cache_key(slide_path)
            image_path, metadata_path = self._get_cache_paths(cache_key)

            # Check if cache entry exists
            if not image_path.exists() or not metadata_path.exists():
                logger.debug(f"Cache miss for: {slide_path.name}")
                return None

            # Load metadata
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Validate cache entry (check modification time)
            current_mtime = slide_path.stat().st_mtime
            cached_mtime = metadata.get("mtime", 0)

            if abs(current_mtime - cached_mtime) > 1.0:  # Allow 1 second tolerance
                logger.debug(f"Cache invalidated (file modified): {slide_path.name}")
                # Clean up stale cache entry
                self._remove_cache_entry(cache_key)
                return None

            # Load thumbnail image
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                logger.warning(f"Failed to load cached thumbnail: {image_path}")
                self._remove_cache_entry(cache_key)
                return None

            logger.debug(f"Cache hit for: {slide_path.name}")
            return pixmap, metadata

        except Exception as e:
            logger.error(f"Error retrieving cached thumbnail: {e}")
            return None

    def put(self, slide_path: Path, pixmap: QPixmap, metadata: Dict) -> bool:
        """
        Store a thumbnail in the cache.

        Args:
            slide_path: Path to the slide file
            pixmap: Thumbnail image to cache
            metadata: Metadata dictionary to store with thumbnail

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Get cache key and paths
            cache_key = self._get_cache_key(slide_path)
            image_path, metadata_path = self._get_cache_paths(cache_key)

            # Add file info to metadata
            if slide_path.exists():
                metadata["mtime"] = slide_path.stat().st_mtime
                metadata["file_path"] = str(slide_path.absolute())
                metadata["cached_at"] = datetime.now().isoformat()

            # Save thumbnail as PNG
            if not pixmap.save(str(image_path), "PNG"):
                logger.error(f"Failed to save thumbnail to cache: {image_path}")
                return False

            # Save metadata as JSON
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"Cached thumbnail for: {slide_path.name}")

            # Check cache size and clean if needed
            self._check_cache_size()

            return True

        except Exception as e:
            logger.error(f"Error caching thumbnail: {e}")
            return False

    def _remove_cache_entry(self, cache_key: str):
        """
        Remove a cache entry (both image and metadata).

        Args:
            cache_key: Cache key to remove
        """
        try:
            image_path, metadata_path = self._get_cache_paths(cache_key)

            if image_path.exists():
                image_path.unlink()

            if metadata_path.exists():
                metadata_path.unlink()

        except Exception as e:
            logger.error(f"Error removing cache entry {cache_key}: {e}")

    def _check_cache_size(self):
        """
        Check total cache size and remove oldest entries if over limit.
        """
        try:
            # Calculate total cache size
            total_size = 0
            cache_entries = []

            for file_path in self.cache_dir.glob("*.png"):
                size = file_path.stat().st_size
                mtime = file_path.stat().st_mtime
                total_size += size
                cache_entries.append((mtime, size, file_path))

                # Also count metadata file
                metadata_path = file_path.with_suffix(".json")
                if metadata_path.exists():
                    total_size += metadata_path.stat().st_size

            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)

            # If over limit, remove oldest entries
            if total_size_mb > self.max_cache_size_mb:
                logger.info(
                    f"Cache size ({total_size_mb:.1f}MB) exceeds limit ({self.max_cache_size_mb}MB)"
                )

                # Sort by modification time (oldest first)
                cache_entries.sort()

                # Remove oldest entries until under limit
                for mtime, size, file_path in cache_entries:
                    if (
                        total_size_mb <= self.max_cache_size_mb * 0.9
                    ):  # Leave 10% buffer
                        break

                    cache_key = file_path.stem
                    self._remove_cache_entry(cache_key)
                    total_size_mb -= size / (1024 * 1024)
                    logger.debug(f"Removed old cache entry: {cache_key}")

                logger.info(f"Cache cleaned. New size: {total_size_mb:.1f}MB")

        except Exception as e:
            logger.error(f"Error checking cache size: {e}")

    def clear(self):
        """
        Clear all cached thumbnails.
        """
        try:
            count = 0
            for file_path in self.cache_dir.glob("*"):
                file_path.unlink()
                count += 1

            logger.info(f"Cleared {count} cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics (count, size, etc.)
        """
        try:
            total_size = 0
            count = 0

            for file_path in self.cache_dir.glob("*.png"):
                total_size += file_path.stat().st_size
                count += 1

                # Also count metadata file
                metadata_path = file_path.with_suffix(".json")
                if metadata_path.exists():
                    total_size += metadata_path.stat().st_size

            return {
                "count": count,
                "size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_cache_size_mb,
                "cache_dir": str(self.cache_dir),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "count": 0,
                "size_mb": 0,
                "max_size_mb": self.max_cache_size_mb,
                "cache_dir": str(self.cache_dir),
            }


# Global cache instance
_global_cache: Optional[ThumbnailCache] = None


def get_thumbnail_cache() -> ThumbnailCache:
    """
    Get the global thumbnail cache instance.

    Returns:
        Global ThumbnailCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = ThumbnailCache()

    return _global_cache
