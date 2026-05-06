from __future__ import annotations

from enum import StrEnum


class SettingsKeys(StrEnum):
    """Centralized QSettings keys used by the workstation UI."""

    GEOMETRY = "geometry"
    WINDOW_STATE = "windowState"
    RECENT_FOLDERS = "recent_folders"
    RECENT_FOLDER_CONFIGS = "recent_folder_configs"
    CONFIG_PRESETS = "config_presets"

    UI_RECENT_FILES_COUNT = "ui/recent_files_count"
    UI_DEFAULT_THUMBNAIL_SIZE = "ui/default_thumbnail_size"
    UI_HIGH_CONTRAST = "ui/high_contrast"
    UI_REDUCED_MOTION = "ui/reduced_motion"

    LEFT_TAB_INDEX = "ui/left_tab_index"
    RIGHT_TAB_INDEX = "ui/right_tab_index"

    CACHE_DIRECTORY = "cache/directory"
    CACHE_MAX_THUMBNAIL_MB = "cache/max_thumbnail_mb"
    CACHE_MAX_TILE_MB = "cache/max_tile_mb"
    CACHE_PERSIST = "cache/persist"

    PERF_PARALLEL_WORKERS = "performance/parallel_workers"
    PERF_TILE_SIZE = "performance/tile_size"
    PERF_MONITORING_ENABLED = "performance/monitoring_enabled"
    PERF_AUTO_REFRESH_SECONDS = "performance/auto_refresh_seconds"

    UI_SHOW_TOOLTIPS = "ui/show_tooltips"
    UI_SHOW_STATUSBAR = "ui/show_statusbar"
    UI_CONFIRM_CLOSE = "ui/confirm_close"


class SplitterKeys(StrEnum):
    TOP_SPLITTER = "layout/topSplitter/sizes"
    OUTER_SPLITTER = "layout/outerSplitter/sizes"
