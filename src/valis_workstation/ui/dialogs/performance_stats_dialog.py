"""
Performance statistics dialog for viewing cache hit rates, memory usage, and metrics.

This dialog provides a comprehensive view of application performance including:
- Thumbnail cache statistics
- Memory usage tracking
- Load time metrics
- Cache management controls

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import logging

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.services.thumbnail_cache import get_thumbnail_cache
from valis_workstation.ui.form_layout_utils import add_form_spacer
from valis_workstation.utils.performance import get_performance_monitor

logger = logging.getLogger(__name__)


class PerformanceStatsDialog(QtWidgets.QDialog):
    """Dialog for displaying performance statistics and cache management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Statistics")
        self.resize(600, 500)

        self._setup_ui()
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self._update_stats)
        self._update_stats()  # Initial update

        # Auto-refresh at the configured interval (default 2 seconds)
        settings = QtCore.QSettings("VALIS", "Workstation")
        refresh_seconds = settings.value(
            "performance/auto_refresh_seconds", 2, type=int
        )
        self._update_timer.start(refresh_seconds * 1000)

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Create tab widget for different stat categories
        tabs = QtWidgets.QTabWidget()

        # Overview tab
        overview_widget = self._create_overview_tab()
        tabs.addTab(overview_widget, "Overview")

        # Thumbnail cache tab
        thumb_widget = self._create_thumbnail_tab()
        tabs.addTab(thumb_widget, "Thumbnail Cache")

        # Memory tab
        memory_widget = self._create_memory_tab()
        tabs.addTab(memory_widget, "Memory")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self._refresh_btn = QtWidgets.QPushButton("Refresh Now")
        self._refresh_btn.clicked.connect(self._update_stats)
        button_layout.addWidget(self._refresh_btn)

        self._clear_thumb_cache_btn = QtWidgets.QPushButton("Clear Thumbnail Cache")
        self._clear_thumb_cache_btn.clicked.connect(self._clear_thumbnail_cache)
        button_layout.addWidget(self._clear_thumb_cache_btn)

        button_layout.addStretch()

        self._close_btn = QtWidgets.QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _create_overview_tab(self):
        """Create the overview tab showing all key metrics."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        # Uptime
        self._uptime_label = QtWidgets.QLabel("0s")
        layout.addRow("Uptime:", self._uptime_label)

        # Current memory
        self._current_mem_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Current Memory:", self._current_mem_label)

        # Peak memory
        self._peak_mem_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Peak Memory:", self._peak_mem_label)

        # Thumbnail cache hit rate
        self._thumb_hit_rate_label = QtWidgets.QLabel("0%")
        layout.addRow("Thumbnail Cache Hit Rate:", self._thumb_hit_rate_label)

        # Average thumbnail load time
        self._thumb_load_time_label = QtWidgets.QLabel("0 ms")
        layout.addRow("Avg Thumbnail Load:", self._thumb_load_time_label)

        # Slides loaded
        self._slides_count_label = QtWidgets.QLabel("0")
        layout.addRow("Slides Loaded:", self._slides_count_label)

        # Registration runs
        self._reg_count_label = QtWidgets.QLabel("0")
        layout.addRow("Registration Runs:", self._reg_count_label)

        add_form_spacer(layout)

        # Progress bars for cache usage
        self._thumb_cache_bar = QtWidgets.QProgressBar()
        layout.addRow("Thumbnail Cache:", self._thumb_cache_bar)

        add_form_spacer(layout)

        return widget

    def _create_thumbnail_tab(self):
        """Create the thumbnail cache statistics tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self._thumb_total_label = QtWidgets.QLabel("0")
        layout.addRow("Total Cached:", self._thumb_total_label)

        self._thumb_size_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Cache Size:", self._thumb_size_label)

        self._thumb_max_size_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Max Size:", self._thumb_max_size_label)

        self._thumb_dir_label = QtWidgets.QLabel("")
        self._thumb_dir_label.setWordWrap(True)
        layout.addRow("Cache Directory:", self._thumb_dir_label)

        self._thumb_hits_label = QtWidgets.QLabel("0")
        layout.addRow("Cache Hits:", self._thumb_hits_label)

        self._thumb_misses_label = QtWidgets.QLabel("0")
        layout.addRow("Cache Misses:", self._thumb_misses_label)

        self._thumb_generated_label = QtWidgets.QLabel("0")
        layout.addRow("Total Generated:", self._thumb_generated_label)

        self._thumb_avg_time_label = QtWidgets.QLabel("0 ms")
        layout.addRow("Avg Load Time:", self._thumb_avg_time_label)

        add_form_spacer(layout)

        return widget

    def _create_memory_tab(self):
        """Create the memory usage tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self._mem_current_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Current:", self._mem_current_label)

        self._mem_peak_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Peak:", self._mem_peak_label)

        self._mem_avg_label = QtWidgets.QLabel("0 MB")
        layout.addRow("Average:", self._mem_avg_label)

        self._mem_samples_label = QtWidgets.QLabel("0")
        layout.addRow("Samples Taken:", self._mem_samples_label)

        add_form_spacer(layout)

        return widget

    def _update_stats(self):
        """Update all statistics displays."""
        try:
            # Get performance monitor
            monitor = get_performance_monitor()
            summary = monitor.get_summary()

            # Overview tab
            uptime = summary.get("uptime_s", 0)
            self._uptime_label.setText(self._format_duration(uptime))

            current_mem = summary.get("current_memory_mb", 0)
            self._current_mem_label.setText(f"{current_mem:.1f} MB")

            peak_mem = summary["memory"]["peak_mb"]
            self._peak_mem_label.setText(f"{peak_mem:.1f} MB")

            thumb_hit_rate = summary["thumbnails"]["cache_hit_rate"]
            self._thumb_hit_rate_label.setText(f"{thumb_hit_rate * 100:.1f}%")

            thumb_load_time = summary["thumbnails"]["avg_load_time_ms"]
            self._thumb_load_time_label.setText(f"{thumb_load_time:.1f} ms")

            slides_count = summary["slides"]["count"]
            self._slides_count_label.setText(str(slides_count))

            reg_count = summary["registration"]["total_runs"]
            self._reg_count_label.setText(str(reg_count))

            # Thumbnail cache tab
            thumb_cache = get_thumbnail_cache()
            thumb_stats = thumb_cache.get_stats()

            self._thumb_total_label.setText(str(thumb_stats["count"]))
            self._thumb_size_label.setText(f"{thumb_stats['size_mb']:.1f} MB")
            self._thumb_max_size_label.setText(f"{thumb_stats['max_size_mb']:.1f} MB")
            self._thumb_dir_label.setText(thumb_stats["cache_dir"])

            self._thumb_hits_label.setText(str(monitor.metrics.thumbnail_cache_hits))
            self._thumb_misses_label.setText(
                str(monitor.metrics.thumbnail_cache_misses)
            )
            self._thumb_generated_label.setText(
                str(len(monitor.metrics.thumbnail_load_times))
            )
            self._thumb_avg_time_label.setText(f"{thumb_load_time:.1f} ms")

            # Thumbnail cache progress bar
            if thumb_stats["max_size_mb"] > 0:
                thumb_pct = int(
                    (thumb_stats["size_mb"] / thumb_stats["max_size_mb"]) * 100
                )
                self._thumb_cache_bar.setValue(thumb_pct)
                self._thumb_cache_bar.setFormat(
                    f"{thumb_stats['size_mb']:.1f} / {thumb_stats['max_size_mb']:.1f} MB ({thumb_pct}%)"
                )

            # Memory tab
            self._mem_current_label.setText(f"{current_mem:.1f} MB")
            self._mem_peak_label.setText(f"{peak_mem:.1f} MB")

            avg_mem = summary["memory"]["avg_mb"]
            self._mem_avg_label.setText(f"{avg_mem:.1f} MB")

            samples = len(monitor.metrics.memory_samples)
            self._mem_samples_label.setText(str(samples))

        except Exception as e:
            logger.error(f"Failed to update performance stats: {e}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def _clear_thumbnail_cache(self):
        """Clear the thumbnail cache."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear Thumbnail Cache",
            "Are you sure you want to clear the thumbnail cache?\n"
            "Thumbnails will need to be regenerated on next load.",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                cache = get_thumbnail_cache()
                cache.clear()
                self._update_stats()

                QtWidgets.QMessageBox.information(
                    self,
                    "Cache Cleared",
                    "Thumbnail cache has been cleared successfully.",
                )

                logger.info("Thumbnail cache cleared by user")

            except Exception as e:
                logger.error(f"Failed to clear thumbnail cache: {e}")
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to clear thumbnail cache:\n{str(e)}"
                )

    def closeEvent(self, event):
        """Stop timer when dialog is closed."""
        self._update_timer.stop()
        super().closeEvent(event)
