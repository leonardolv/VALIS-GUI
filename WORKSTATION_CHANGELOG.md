# VALIS Workstation Changelog

## 2026-08-18

### Fixed
- The Preferences dialog persisted 13 settings to `QSettings` that nothing in the application ever read back, so every field was a no-op even after a restart — `_on_preferences_changed`'s "Some preference changes require restarting the application to take effect" was true of nothing. Wired seven of them into their real call sites (`src/valis_workstation/main_window.py`, `src/valis_workstation/services/thumbnail_cache.py`, `src/valis_workstation/utils/tile_cache.py`, `src/valis_workstation/ui/dialogs/performance_stats_dialog.py`):
	- `performance/parallel_workers` — thumbnail generation's `ThreadPoolExecutor` was hardcoded to `min(4, total_slides)`.
	- `ui/recent_files_count` — the recent-folders list was hardcoded to `recent[:10]`.
	- `ui/confirm_close` — the checkbox existed with no confirmation dialog behind it anywhere; `closeEvent` now asks before closing when enabled.
	- `ui/show_statusbar` — the status bar was always shown regardless of the setting.
	- `cache/directory` / `cache/max_thumbnail_mb` — `get_thumbnail_cache()` always constructed `ThumbnailCache()` with its built-in defaults (`~/.valis_cache`, 500 MB), ignoring both fields.
	- `cache/max_tile_mb` / `performance/tile_size` — same shape in `get_tile_cache()`, always called with no arguments from both its call sites.
	- `ui/default_thumbnail_size` — thumbnail generation was hardcoded to `max_size=512`.
	- `performance/auto_refresh_seconds` — the Performance Statistics dialog's refresh timer was hardcoded to 2000 ms.

	Three settings remain unwired and are not fixed here: `ui/show_tooltips` (would need an application-wide event filter, not a single call site), `cache/persist` (would need cache-clearing-on-exit logic, a behavior decision rather than a wiring fix), and `performance/monitoring_enabled` (moot — `PerformanceMonitor.track_thumbnail_load`/etc. have no caller anywhere in the app, so its metrics are always empty regardless of the toggle; that's a separate, deeper gap worth its own pass). See `AGENT_TASK_LOG.md`'s matching entry.

### Testing
- `QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/` (this environment's `xvfb-run` aborts on plain `QApplication()` construction even on a clean checkout — a pre-existing sandbox/display issue, not a regression; `QT_QPA_PLATFORM=offscreen` sidesteps it without `xvfb` at all): **313 passed, 4 failed** — the 4 failures (`test_pipeline.py::TestBuildRegistrarKwargs`) reproduce identically with this change's files stashed, caused by `torch` not being installed in this environment (`valis.feature_detectors not importable: No module named 'torch'`), unrelated to this change. Targeted subset most relevant to the fix (`test_thumbnail_cache.py`, `test_app.py`, `test_gui_components.py`, `test_all_features.py`): **153 passed, 0 failed**.

## 2026-03-22

### Added
- First-run setup wizard to capture default project name and output profile (`src/valis_workstation/app.py`, `src/valis_workstation/ui/dialogs/first_run_wizard.py`).
- Configuration presets (save/load/delete) and output profile templates (`Custom`, `WSI Archive`, `Fast Review`, `Publication`) in Properties (`src/valis_workstation/ui/properties_dock.py`).
- Preflight estimate step before registration confirmation, including input size/output estimate/time estimate (`src/valis_workstation/main_window.py`).
- Resume action for restarting the last run context (`src/valis_workstation/main_window.py`).
- Session bundle export (`.zip`) containing `session_summary.json` and current log file (`src/valis_workstation/main_window.py`).
- Diagnostics dialog for environment/runtime summary (`src/valis_workstation/ui/dialogs/diagnostics_dialog.py`, `src/valis_workstation/main_window.py`).
- Stage/progress/ETA support in loading overlay (`src/valis_workstation/ui/splash_screen.py`).
- Slide preview filter/sort controls and thumbnail refresh improvements (`src/valis_workstation/ui/slide_preview_dock.py`).
- Blink viewer mode selector (`Blink`, `Side-by-side`, `Swipe`) (`src/valis_workstation/ui/dialogs/blink_viewer.py`).
- Layer controls quality-of-life tools: search, lock edits, solo selected, reset opacity (`src/valis_workstation/ui/layer_controls_dock.py`).
- Form-layout spacer helper for cross-layout compatibility (`src/valis_workstation/ui/form_layout_utils.py`).

### Changed
- Constants groups migrated to `StrEnum` with helper methods for iteration and label mapping (`src/valis_workstation/constants.py`).
- Recent folders menu now surfaces missing-folder state and supports linked folder->config reopening (`src/valis_workstation/main_window.py`).
- Status dock now includes stage indicator and safer cancel callback rebinding (`src/valis_workstation/ui/status_dock.py`).

### Fixed
- Resolved dialog crash caused by invalid `QFormLayout.addStretch()` usage (`src/valis_workstation/ui/dialogs/performance_stats_dialog.py`, `src/valis_workstation/ui/dialogs/preferences_dialog.py`).
- Hardened layer controls for test/fallback viewers where `layers` is a plain list and event hooks are absent (`src/valis_workstation/ui/layer_controls_dock.py`).
- Stabilized UI tests by stubbing modal dialogs and fixing thumbnail monkeypatch signatures (`tests/test_all_features.py`).
- Reconciled validation behavior expectations for empty slide lists in comprehensive tests (`tests/test_all_features.py`).

### Testing
- Added/updated regression coverage for:
	- Form-layout dialogs construction
	- Output profile templates
	- Main window startup performance smoke guard
	- Layer controls and workflow interactions (`tests/test_all_features.py`)
- Full suite status after integration: `316 passed`.

### Notes
- Comparison modes in Blink viewer are practical UI-level modes; future iterations can deepen semantic rendering behavior.
