# VALIS Workstation Changelog

## 2026-08-19 (3)

### Removed
- Resolved the Backlog item filed by 2026-08-19 (2) — "worth deciding whether `TileCache` is meant to be wired into real tile rendering (a real, larger feature) or removed as speculative infrastructure" — by removing it. The real image display goes through napari's own `viewer.open()` (`MainWindow`); nothing in the app calls `TiledImageLoader.get_tile`/`get_region` (the only methods that would actually read a WSI tile and populate the cache) or `LRUTileCache.get`/`put` directly, and neither class had any test coverage of its own — wiring it into rendering would duplicate napari's own multiscale reading with no code path to hang it on, which is the "real, larger feature" the Backlog entry deferred, not a few-hours fix.

	Removed:
	- `src/valis_workstation/utils/tile_cache.py` in full (`TileKey`, `LRUTileCache`, `TiledImageLoader`, `get_tile_cache`).
	- `PerformanceMonitor.track_tile_load` and the `tile_cache_hits`/`tile_cache_misses`/`tile_load_times` fields on `PerformanceMetrics`, plus the `"tiles"` key of `get_summary()` and its two log/status-bar readers (`src/valis_workstation/utils/performance.py`) — this tracker had no caller either, a fact the 2026-08-19 (2) entry already noted when it wired the other three.
	- The Performance Statistics dialog's "Tile Cache" tab (7 fields + progress bar), its Overview-tab "Tile Cache Hit Rate" row, and the "Clear Tile Cache" button (`src/valis_workstation/ui/dialogs/performance_stats_dialog.py`) — all three showed permanently-zero numbers and the clear button cleared a cache nothing had ever put anything into, which is user-visible-misleading rather than merely inert.
	- The Preferences "Max Tile Cache" spinbox (`cache/max_tile_mb`) (`src/valis_workstation/ui/dialogs/preferences_dialog.py`) — it *was* read (into `LRUTileCache`'s constructor, `get_tile_cache()`'s default-arg fallback), which is a subtler case than the other "control that does not control" fixes in this log: the setting genuinely reached the object it was meant to configure, but that object's memory limit has no observable effect on anything, because nothing ever populates it. A setting a user can change with no way to ever notice the change is the same bug from their side of the screen.

	- The Preferences "Tile Size (pixels)" combo box (`performance/tile_size`) — its *only* consumer was `get_tile_cache()`'s default-arg fallback, so deleting that module orphaned this setting too; not a pre-existing gap, a consequence of removing the field above it. (Registration's own, unrelated tile size — `properties_dock.py`'s `_tile_size_spin` feeding `RegistrationConfig.tile_size`/`save_kwargs["tile_wh"]` — is a different setting under a different key and is untouched.)

### Testing
- Removed the two tests exercising the deleted surface: `TestPerformanceMonitor::test_track_tile` and the `s["tiles"]["cache_hit_rate"]` assertion in `TestPerformanceMetrics::test_empty_summary` (`tests/test_utils.py`).
- `python -c "import ast; ast.parse(...)"` on all four edited files: syntax OK.
- `grep -rn "tile_cache\|TileCache\|TiledImageLoader\|max_tile" src/ tests/`: zero remaining references outside this changelog and `AGENT_TASK_LOG.md`.
- Full suite: see `AGENT_TASK_LOG.md`'s matching entry for the run.

## 2026-08-19 (2)

### Fixed
- `PerformanceMonitor.track_thumbnail_load`/`track_tile_load`/`track_registration`/`track_slides_loaded` had no caller anywhere in the app, so `PerformanceStatsDialog`'s numbers were always zero/empty regardless of real activity or the "Enable performance monitoring" checkbox (`performance/monitoring_enabled`, itself unread until now). Wired three real call sites:
	- Thumbnails — `generate_thumbnail` (`src/valis_workstation/services/thumbnail_generator.py`) now times itself and tracks both a cache hit and a fresh generation.
	- Slides — `MainWindow._load_thumbnails_parallel` (`src/valis_workstation/main_window.py`) tracks the whole folder load using the `started_at` timestamp it already computed for the loading overlay's ETA.
	- Registration — `ValisWorker.run` (`src/valis_workstation/workers/valis_worker.py`) times the `run_valis_pipeline` call and tracks it right before emitting `finished`.

	All four trackers (plus `sample_memory`'s recording half) now check `performance/monitoring_enabled` via a new `_monitoring_enabled()` helper (`src/valis_workstation/utils/performance.py`), read fresh from `QSettings` on every call so toggling the Preferences checkbox takes effect immediately.

	Tiles are a separate, deeper gap and were **not** wired here: `get_tile_cache()` has no caller anywhere in the app outside `utils/tile_cache.py` and the stats dialog itself, so there is no real tile-loading call site to track — that dialog tab already shows correct numbers from `TileCache`'s own internal hit/miss counters. Filed to `AGENT_TASK_LOG.md`'s Backlog as its own item (whether `TileCache` should be wired into real rendering or removed as speculative infrastructure).

### Testing
- New `tests/test_performance_monitoring_wiring.py` (15 tests).
- Targeted: `test_performance_monitoring_wiring.py` + `test_thumbnail_cache.py` + `test_worker.py` + `test_preferences_wiring_followups.py`: **34 passed, 0 failed**.
- Full suite: **337 passed, 4 failed** — the 4 (`test_pipeline.py::TestBuildRegistrarKwargs`) reproduce identically on the unmodified tree in this environment (a `SimpleITK` import gap beyond what `torch`/`kornia`/`libvips42` cover), unrelated to this change.
- `ruff check src/`: 20 findings both before and after.

## 2026-08-19

### Fixed
- The last two Preferences fields left disconnected by 2026-08-18's pass, both of which needed a design decision rather than a call site:
	- `ui/show_tooltips` — no single call site can own "was a tooltip shown", since Qt dispatches `QEvent.Type.ToolTip` to whichever widget is under the cursor. Added `app._ToolTipSuppressionFilter`, a `QObject` event filter installed on the `QApplication` (`src/valis_workstation/app.py`) that consumes every `ToolTip` event while the setting is off, re-reading `QSettings` on each event so a Preferences change applies immediately without a restart.
	- `cache/persist` ("Keep cache between sessions") — `MainWindow.closeEvent` now clears `ThumbnailCache`'s on-disk contents when unchecked (`src/valis_workstation/main_window.py`), in its own `try`/`except` so a clear failure can't block the window from closing.

### Testing
- New `tests/test_preferences_wiring_followups.py` (9 tests) covering both.
- This environment was missing `torch` and the system `libvips.so.42` library that the 2026-08-18 run's environment also lacked (`apt-get install libvips42` resolves the latter); with both present, the four `test_pipeline.py::TestBuildRegistrarKwargs` failures noted in that entry as unrelated now pass as well.
- Full suite: **326 passed, 0 failed** (up from 313/4 — the 13 new tests plus the 4 now-environment-satisfied ones account for the difference; 0 failures caused by this change).
- `ruff check` on the two touched source files: finding count unchanged.

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
