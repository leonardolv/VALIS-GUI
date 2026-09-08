"""
Performance monitoring and metrics tracking for VALIS Workstation.

This module provides utilities for tracking and reporting performance metrics
such as load times, memory usage, cache hit rates, and other statistics.

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


def _monitoring_enabled() -> bool:
    """Whether Preferences > "Enable performance monitoring" is on.

    Re-read from ``QSettings`` on every call rather than cached, so toggling
    the checkbox takes effect immediately without restarting the app — same
    approach as the app's ``ui/show_tooltips`` filter. Imports Qt lazily and
    fails open (monitoring enabled) if it is unavailable, since this module
    otherwise has no Qt dependency and a missing/broken settings backend
    should not be what silently disables metrics collection.
    """
    try:
        from PySide6.QtCore import QSettings

        return bool(
            QSettings("VALIS", "Workstation").value(
                "performance/monitoring_enabled", True, type=bool
            )
        )
    except Exception:
        return True


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    # Thumbnail generation metrics
    thumbnail_load_times: List[float] = field(default_factory=list)
    thumbnail_cache_hits: int = 0
    thumbnail_cache_misses: int = 0

    # Registration metrics
    registration_times: List[float] = field(default_factory=list)

    # Memory metrics
    peak_memory_mb: float = 0.0
    memory_samples: List[float] = field(default_factory=list)

    # Slide loading metrics
    slide_count: int = 0
    total_slide_load_time: float = 0.0

    def get_summary(self) -> Dict:
        """Get a summary of all metrics."""
        summary = {
            "thumbnails": {
                "total_generated": len(self.thumbnail_load_times),
                "avg_load_time_ms": (
                    sum(self.thumbnail_load_times)
                    / len(self.thumbnail_load_times)
                    * 1000
                    if self.thumbnail_load_times
                    else 0
                ),
                "cache_hit_rate": (
                    self.thumbnail_cache_hits
                    / (self.thumbnail_cache_hits + self.thumbnail_cache_misses)
                    if (self.thumbnail_cache_hits + self.thumbnail_cache_misses) > 0
                    else 0
                ),
            },
            "registration": {
                "total_runs": len(self.registration_times),
                "avg_time_s": (
                    sum(self.registration_times) / len(self.registration_times)
                    if self.registration_times
                    else 0
                ),
            },
            "memory": {
                "peak_mb": self.peak_memory_mb,
                "avg_mb": (
                    sum(self.memory_samples) / len(self.memory_samples)
                    if self.memory_samples
                    else 0
                ),
            },
            "slides": {
                "count": self.slide_count,
                "avg_load_time_s": (
                    self.total_slide_load_time / self.slide_count
                    if self.slide_count > 0
                    else 0
                ),
            },
        }

        return summary


class PerformanceMonitor:
    """
    Performance monitoring system for tracking and reporting metrics.

    This class provides context managers and utilities for tracking various
    performance metrics throughout the application.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = PerformanceMetrics()
        self._start_time = time.time()
        self._memory_process = psutil.Process()

        logger.info("Performance monitoring initialized")

    def track_thumbnail_load(self, duration: float, from_cache: bool = False) -> None:
        """
        Track thumbnail loading time.

        Parameters
        ----------
        duration : float
            Load time in seconds
        from_cache : bool
            Whether loaded from cache
        """
        if not _monitoring_enabled():
            return
        self.metrics.thumbnail_load_times.append(duration)

        if from_cache:
            self.metrics.thumbnail_cache_hits += 1
        else:
            self.metrics.thumbnail_cache_misses += 1

        logger.debug(
            f"Thumbnail load: {duration * 1000:.1f}ms "
            f"({'cache' if from_cache else 'generated'})"
        )

    def track_registration(self, duration: float) -> None:
        """
        Track registration time.

        Parameters
        ----------
        duration : float
            Registration time in seconds
        """
        if not _monitoring_enabled():
            return
        self.metrics.registration_times.append(duration)
        logger.info(f"Registration completed in {duration:.1f}s")

    def track_slides_loaded(self, count: int, duration: float) -> None:
        """
        Track slide loading.

        Parameters
        ----------
        count : int
            Number of slides loaded
        duration : float
            Total load time in seconds
        """
        if not _monitoring_enabled() or count <= 0:
            return
        self.metrics.slide_count += count
        self.metrics.total_slide_load_time += duration

        logger.info(
            f"Loaded {count} slides in {duration:.2f}s "
            f"({duration / count:.2f}s per slide)"
        )

    def sample_memory(self) -> float:
        """
        Sample current memory usage.

        Returns
        -------
        float
            Current memory usage in MB
        """
        try:
            # Get memory info
            mem_info = self._memory_process.memory_info()
            current_mb = mem_info.rss / (1024 * 1024)

            # The instantaneous reading is returned either way — it is a live
            # process stat, not an accumulated metric — but recording it into
            # the tracked history (what "peak"/"average" are computed from)
            # honors the same monitoring toggle every other tracker does.
            if _monitoring_enabled():
                self.metrics.memory_samples.append(current_mb)

                if current_mb > self.metrics.peak_memory_mb:
                    self.metrics.peak_memory_mb = current_mb

            return current_mb

        except Exception as e:
            logger.error(f"Failed to sample memory: {e}")
            return 0.0

    def get_summary(self) -> Dict:
        """
        Get performance summary.

        Returns
        -------
        Dict
            Performance metrics summary
        """
        summary = self.metrics.get_summary()

        # Add uptime
        summary["uptime_s"] = time.time() - self._start_time

        # Add current memory
        summary["current_memory_mb"] = self.sample_memory()

        return summary

    def log_summary(self) -> None:
        """Log performance summary to logger."""
        summary = self.get_summary()

        logger.info("=== Performance Summary ===")

        # Thumbnails
        thumb = summary["thumbnails"]
        logger.info(
            f"Thumbnails: {thumb['total_generated']} generated, "
            f"{thumb['avg_load_time_ms']:.1f}ms avg, "
            f"{thumb['cache_hit_rate'] * 100:.1f}% cache hit rate"
        )

        # Registration
        reg = summary["registration"]
        if reg["total_runs"] > 0:
            logger.info(
                f"Registration: {reg['total_runs']} runs, "
                f"{reg['avg_time_s']:.1f}s average"
            )

        # Memory
        mem = summary["memory"]
        logger.info(
            f"Memory: {summary['current_memory_mb']:.1f}MB current, "
            f"{mem['peak_mb']:.1f}MB peak, "
            f"{mem['avg_mb']:.1f}MB average"
        )

        # Slides
        slides = summary["slides"]
        if slides["count"] > 0:
            logger.info(
                f"Slides: {slides['count']} loaded, "
                f"{slides['avg_load_time_s']:.2f}s average load time"
            )

        logger.info(f"Uptime: {summary['uptime_s']:.1f}s")
        logger.info("=" * 30)

    def get_status_message(self) -> str:
        """
        Get a concise status message for display in status bar.

        Returns
        -------
        str
            Status message
        """
        current_mem = self.sample_memory()

        # Build status message
        parts = []

        # Memory
        parts.append(f"Mem: {current_mem:.0f}MB")

        # Thumbnail cache hit rate
        if self.metrics.thumbnail_cache_hits + self.metrics.thumbnail_cache_misses > 0:
            hit_rate = self.metrics.thumbnail_cache_hits / (
                self.metrics.thumbnail_cache_hits + self.metrics.thumbnail_cache_misses
            )
            parts.append(f"Thumb Cache: {hit_rate * 100:.0f}%")

        return " | ".join(parts)


class TimingContext:
    """
    Context manager for timing operations.

    Example
    -------
    >>> with TimingContext("Load thumbnail") as timer:
    ...     # Do work
    ...     pass
    >>> print(f"Took {timer.duration}s")
    """

    def __init__(self, operation_name: str, log_result: bool = True):
        """
        Initialize timing context.

        Parameters
        ----------
        operation_name : str
            Name of the operation being timed
        log_result : bool
            Whether to log the result when complete
        """
        self.operation_name = operation_name
        self.log_result = log_result
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: float = 0.0

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        logger.debug(f"Started: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log result."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        if self.log_result:
            if exc_type is None:
                logger.debug(
                    f"Completed: {self.operation_name} in {self.duration * 1000:.1f}ms"
                )
            else:
                logger.debug(
                    f"Failed: {self.operation_name} after {self.duration * 1000:.1f}ms"
                )

        return False  # Don't suppress exceptions


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns
    -------
    PerformanceMonitor
        Global performance monitor
    """
    global _global_monitor

    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()

    return _global_monitor


def log_performance_summary() -> None:
    """Log the current performance summary."""
    monitor = get_performance_monitor()
    monitor.log_summary()


def get_performance_status() -> str:
    """
    Get performance status message.

    Returns
    -------
    str
        Status message for display
    """
    monitor = get_performance_monitor()
    return monitor.get_status_message()
