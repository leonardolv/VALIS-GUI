"""
User preferences dialog for configuring application settings.

Allows configuration of:
- Cache settings (directory, max size)
- Performance settings (parallel workers, tile size)
- UI preferences

Settings are persisted using QSettings.

Author: VALIS Workstation Team
Date: 2026-01-11
"""

import logging
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.ui.form_layout_utils import add_form_spacer

logger = logging.getLogger(__name__)


class PreferencesDialog(QtWidgets.QDialog):
    """Dialog for editing application preferences."""

    # Signal emitted when preferences change
    preferences_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(500, 400)

        self._settings = QtCore.QSettings("VALIS", "Workstation")

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Create tab widget for different preference categories
        tabs = QtWidgets.QTabWidget()

        # Cache tab
        cache_widget = self._create_cache_tab()
        tabs.addTab(cache_widget, "Cache")

        # Performance tab
        perf_widget = self._create_performance_tab()
        tabs.addTab(perf_widget, "Performance")

        # UI tab
        ui_widget = self._create_ui_tab()
        tabs.addTab(ui_widget, "User Interface")

        layout.addWidget(tabs)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults
        )

        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._restore_defaults)

        layout.addWidget(button_box)

    def _create_cache_tab(self):
        """Create the cache settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        # Thumbnail cache directory
        cache_dir_layout = QtWidgets.QHBoxLayout()
        self._cache_dir_edit = QtWidgets.QLineEdit()
        self._cache_dir_edit.setPlaceholderText("Default: ~/.valis_cache")
        cache_dir_layout.addWidget(self._cache_dir_edit)

        browse_btn = QtWidgets.QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_cache_dir)
        cache_dir_layout.addWidget(browse_btn)

        layout.addRow("Cache Directory:", cache_dir_layout)

        # Max thumbnail cache size
        self._max_thumb_cache_spin = QtWidgets.QSpinBox()
        self._max_thumb_cache_spin.setRange(10, 10000)
        self._max_thumb_cache_spin.setSuffix(" MB")
        self._max_thumb_cache_spin.setValue(500)
        layout.addRow("Max Thumbnail Cache:", self._max_thumb_cache_spin)

        # Max tile cache size
        self._max_tile_cache_spin = QtWidgets.QSpinBox()
        self._max_tile_cache_spin.setRange(100, 10000)
        self._max_tile_cache_spin.setSuffix(" MB")
        self._max_tile_cache_spin.setValue(1024)
        layout.addRow("Max Tile Cache:", self._max_tile_cache_spin)

        # Cache persistence
        self._persist_cache_check = QtWidgets.QCheckBox("Keep cache between sessions")
        self._persist_cache_check.setChecked(True)
        layout.addRow("", self._persist_cache_check)

        add_form_spacer(layout)

        # Info label
        info_label = QtWidgets.QLabel(
            "Note: Changes to cache settings require restarting the application."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addRow(info_label)

        add_form_spacer(layout)

        return widget

    def _create_performance_tab(self):
        """Create the performance settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        # Parallel thumbnail workers
        self._parallel_workers_spin = QtWidgets.QSpinBox()
        self._parallel_workers_spin.setRange(1, 16)
        self._parallel_workers_spin.setValue(4)
        layout.addRow("Parallel Thumbnail Workers:", self._parallel_workers_spin)

        # Tile size
        self._tile_size_combo = QtWidgets.QComboBox()
        self._tile_size_combo.addItems(["256", "512", "1024", "2048"])
        self._tile_size_combo.setCurrentText("512")
        layout.addRow("Tile Size (pixels):", self._tile_size_combo)

        # Enable performance monitoring
        self._perf_monitoring_check = QtWidgets.QCheckBox(
            "Enable performance monitoring"
        )
        self._perf_monitoring_check.setChecked(True)
        layout.addRow("", self._perf_monitoring_check)

        # Auto-refresh interval
        self._auto_refresh_spin = QtWidgets.QSpinBox()
        self._auto_refresh_spin.setRange(1, 60)
        self._auto_refresh_spin.setSuffix(" seconds")
        self._auto_refresh_spin.setValue(2)
        layout.addRow("Stats Auto-Refresh:", self._auto_refresh_spin)

        add_form_spacer(layout)

        # Info label
        info_label = QtWidgets.QLabel(
            "Higher worker counts speed up thumbnail generation but use more memory.\n"
            "Larger tile sizes reduce the number of tiles but use more memory per tile."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addRow(info_label)

        add_form_spacer(layout)

        return widget

    def _create_ui_tab(self):
        """Create the UI preferences tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        # Show tooltips
        self._show_tooltips_check = QtWidgets.QCheckBox("Show tooltips")
        self._show_tooltips_check.setChecked(True)
        layout.addRow("", self._show_tooltips_check)

        # Show status bar
        self._show_statusbar_check = QtWidgets.QCheckBox("Show status bar")
        self._show_statusbar_check.setChecked(True)
        layout.addRow("", self._show_statusbar_check)

        # Confirm before closing
        self._confirm_close_check = QtWidgets.QCheckBox("Confirm before closing")
        self._confirm_close_check.setChecked(False)
        layout.addRow("", self._confirm_close_check)

        # Recent files count
        self._recent_files_spin = QtWidgets.QSpinBox()
        self._recent_files_spin.setRange(5, 20)
        self._recent_files_spin.setValue(10)
        layout.addRow("Recent Files to Remember:", self._recent_files_spin)

        # Default thumbnail size
        self._default_thumb_size_spin = QtWidgets.QSpinBox()
        self._default_thumb_size_spin.setRange(128, 1024)
        self._default_thumb_size_spin.setSingleStep(64)
        self._default_thumb_size_spin.setValue(512)
        layout.addRow("Default Thumbnail Size:", self._default_thumb_size_spin)

        add_form_spacer(layout)

        return widget

    def _browse_cache_dir(self):
        """Browse for cache directory."""
        current_dir = self._cache_dir_edit.text()
        if not current_dir:
            current_dir = str(Path.home() / ".valis_cache")

        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Cache Directory", current_dir
        )

        if directory:
            self._cache_dir_edit.setText(directory)

    def _load_settings(self):
        """Load settings from QSettings."""
        # Cache settings
        cache_dir = self._settings.value("cache/directory", "")
        self._cache_dir_edit.setText(cache_dir)

        max_thumb_cache = self._settings.value("cache/max_thumbnail_mb", 500, type=int)
        self._max_thumb_cache_spin.setValue(max_thumb_cache)

        max_tile_cache = self._settings.value("cache/max_tile_mb", 1024, type=int)
        self._max_tile_cache_spin.setValue(max_tile_cache)

        persist_cache = self._settings.value("cache/persist", True, type=bool)
        self._persist_cache_check.setChecked(persist_cache)

        # Performance settings
        parallel_workers = self._settings.value(
            "performance/parallel_workers", 4, type=int
        )
        self._parallel_workers_spin.setValue(parallel_workers)

        tile_size = self._settings.value("performance/tile_size", 512, type=int)
        self._tile_size_combo.setCurrentText(str(tile_size))

        perf_monitoring = self._settings.value(
            "performance/monitoring_enabled", True, type=bool
        )
        self._perf_monitoring_check.setChecked(perf_monitoring)

        auto_refresh = self._settings.value(
            "performance/auto_refresh_seconds", 2, type=int
        )
        self._auto_refresh_spin.setValue(auto_refresh)

        # UI settings
        show_tooltips = self._settings.value("ui/show_tooltips", True, type=bool)
        self._show_tooltips_check.setChecked(show_tooltips)

        show_statusbar = self._settings.value("ui/show_statusbar", True, type=bool)
        self._show_statusbar_check.setChecked(show_statusbar)

        confirm_close = self._settings.value("ui/confirm_close", False, type=bool)
        self._confirm_close_check.setChecked(confirm_close)

        recent_files = self._settings.value("ui/recent_files_count", 10, type=int)
        self._recent_files_spin.setValue(recent_files)

        default_thumb_size = self._settings.value(
            "ui/default_thumbnail_size", 512, type=int
        )
        self._default_thumb_size_spin.setValue(default_thumb_size)

    def _save_and_accept(self):
        """Save settings and close dialog."""
        # Cache settings
        self._settings.setValue("cache/directory", self._cache_dir_edit.text())
        self._settings.setValue(
            "cache/max_thumbnail_mb", self._max_thumb_cache_spin.value()
        )
        self._settings.setValue("cache/max_tile_mb", self._max_tile_cache_spin.value())
        self._settings.setValue("cache/persist", self._persist_cache_check.isChecked())

        # Performance settings
        self._settings.setValue(
            "performance/parallel_workers", self._parallel_workers_spin.value()
        )
        self._settings.setValue(
            "performance/tile_size", int(self._tile_size_combo.currentText())
        )
        self._settings.setValue(
            "performance/monitoring_enabled", self._perf_monitoring_check.isChecked()
        )
        self._settings.setValue(
            "performance/auto_refresh_seconds", self._auto_refresh_spin.value()
        )

        # UI settings
        self._settings.setValue(
            "ui/show_tooltips", self._show_tooltips_check.isChecked()
        )
        self._settings.setValue(
            "ui/show_statusbar", self._show_statusbar_check.isChecked()
        )
        self._settings.setValue(
            "ui/confirm_close", self._confirm_close_check.isChecked()
        )
        self._settings.setValue(
            "ui/recent_files_count", self._recent_files_spin.value()
        )
        self._settings.setValue(
            "ui/default_thumbnail_size", self._default_thumb_size_spin.value()
        )

        # Sync settings to disk
        self._settings.sync()

        # Emit signal
        self.preferences_changed.emit()

        logger.info("Preferences saved")

        self.accept()

    def _restore_defaults(self):
        """Restore default settings."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore default settings?\n"
            "This will reset all preferences to their default values.",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Restore defaults
            self._cache_dir_edit.setText("")
            self._max_thumb_cache_spin.setValue(500)
            self._max_tile_cache_spin.setValue(1024)
            self._persist_cache_check.setChecked(True)

            self._parallel_workers_spin.setValue(4)
            self._tile_size_combo.setCurrentText("512")
            self._perf_monitoring_check.setChecked(True)
            self._auto_refresh_spin.setValue(2)

            self._show_tooltips_check.setChecked(True)
            self._show_statusbar_check.setChecked(True)
            self._confirm_close_check.setChecked(False)
            self._recent_files_spin.setValue(10)
            self._default_thumb_size_spin.setValue(512)

            logger.info("Preferences reset to defaults")
