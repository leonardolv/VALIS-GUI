# VALIS Workstation Changelog

## 2026-09-22

### Fixed
- `BlinkViewerDialog`'s auto-blink `QTimer` (600ms interval, toggles two napari layers' visibility) kept running forever after the dialog was dismissed via its own "Close" standard button or the Escape key — the two ordinary ways to close it. The timer was only ever stopped from `closeEvent`, but `QDialog.reject()`/`.accept()` (what `QDialogButtonBox.StandardButton.Close`'s `rejected` signal and Escape both call) do **not** invoke `closeEvent` — only a real `close()`/window-X-button does, confirmed empirically with an offscreen-Qt probe. Since the dialog is parented to `MainWindow`, "closing" it this way only `hide()`s it; the C++ object (and its timer) stays alive for the rest of the session, so it kept toggling layer visibility in the background indefinitely — a CPU/background-behavior leak that compounds with every Blink session a user starts and dismisses normally. The one existing test for this (`test_close_stops_timer`) called `dialog.close()` directly, which is exactly the one path that already worked, so the bug shipped unnoticed. Fixed by also connecting `self.finished` (emitted by both `accept()` and `reject()`) to the same stop-the-timer cleanup, alongside the existing `closeEvent` override — together they cover every way the dialog can be dismissed.

### Testing
- Two new `tests/test_all_features.py::TestBlinkViewerDialog` tests (`test_reject_stops_timer`, `test_accept_stops_timer`) drive the dialog via `reject()`/`accept()` rather than `close()`, reproducing the actual "Close" button / Escape path; a third (`test_reject_resets_toggle_and_never_started`) pins that dismissing without ever starting Blink stays a no-op.
- The two reproducing tests fail on the pre-fix tree (`git stash` of just `blink_viewer.py`, rerun, then restored) with `_timer.isActive()` still `True` after `reject()`/`accept()`; pass after the fix.
- Full suite: `QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **432 passed** (was 429), 0 regressions.
- `ruff check src/valis_workstation/ui/dialogs/blink_viewer.py tests/test_all_features.py` — 0 findings in the touched code (the file's 7 pre-existing findings are all unrelated, unmoved lines, confirmed by line number). `ruff check src/` (whole tree): 123 findings before and after, 0 new.

- `MergeSlidesDialog`'s "Average" overlap-handling option didn't actually average duplicate-named channels — it asked VALIS to keep every duplicate as its own separate band (`drop_duplicates=False`; VALIS has no averaging mode of its own) and stopped there, so a merge with two slides both labeled e.g. "DAPI" saved *two* DAPI bands rather than one combined band, contradicting the option's own tooltip ("Average: Average overlapping values"). New `_average_duplicate_bands()` in `services/merge_slides.py` collapses same-named bands into their pixelwise mean (one band per unique name, first-occurrence order — the same shape "First"/"Last" already produce), run after VALIS builds the (still-duplicated) image and before it is saved. When averaging actually drops bands, the OME-XML metadata is rebuilt for the reduced channel list via a new `_rebuild_ome_xml_for_channels()` helper (reproducing VALIS's own OME-XML construction), so the saved file's header always matches its real band count. The common case (no channel name actually repeats) is detected up front from `channel_name_dict` and still takes the original direct-to-disk save path unchanged — no added cost when there's nothing to average. Averaging runs before normalizing when both are requested, so a shared "Normalize intensities" stretch is computed from the merged (not the pre-merge duplicated) signal.

- `SettingsKeys.CACHE_MAX_TILE_MB`/`PERF_TILE_SIZE` were orphaned `QSettings` enum members left over from the 2026-08-19 removal of `utils/tile_cache.py` (which deleted the Preferences "Max Tile Cache" spinbox and "Tile Size (pixels)" combo — their only readers/writers — but not the two enum members themselves). Harmless (nothing read or wrote either key), but genuine dead code. Removed both.

### Testing
- New `tests/test_merge_slides_service.py::TestAverageDuplicateBands` (5 tests) for `_average_duplicate_bands` itself (no-op when nothing repeats — same objects returned, not copies; a two-way duplicate averaged alongside an untouched unique band; a three-way duplicate; result order follows first occurrence; the single-band `.copy(interpretation=...)` path), plus `::TestMergeRegisteredSlidesAverageDuplicateHandling` (4 tests) exercising `merge_registered_slides` end to end: duplicate DAPI bands are averaged and saved under a rebuilt, matching OME-XML; a config with no actual duplicates stays on the original direct-save path (`registrar.get_ref_slide` never even called); averaging runs before normalizing (checked by an input that would produce a different, wrong result the other way round); cancellation after the build still raises before any averaging/OME-XML/save work happens.
- All 9 new tests fail to collect (`ImportError: cannot import name '_average_duplicate_bands'`) on the pre-fix tree (`git stash` of just `services/merge_slides.py`, rerun, then restored).
- Full suite: `QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **429 passed** (was 420), 0 regressions.
- `ruff check src/valis_workstation/services/merge_slides.py tests/test_merge_slides_service.py` — 0 findings. `ruff check src/` (whole tree, same binary both sides): 16 findings before and after, 0 new.

- New `tests/test_settings_keys.py` (7 tests, for the `CACHE_MAX_TILE_MB`/`PERF_TILE_SIZE` fix above): pins the two names no longer resolving on `SettingsKeys` and their literal key strings no longer appearing anywhere in `src/`, plus a general regression guard asserting every remaining `SettingsKeys`/`SplitterKeys` member (by literal string value or direct enum reference) is used somewhere outside `settings_keys.py` — so a future dead member added the same way is caught automatically rather than needing another manual audit.
- 4 of those 7 fail on the pre-fix tree (`git stash` of just `settings_keys.py`, rerun, then restored) — including the general sweep, which independently flagged exactly the two known-dead names.
- Full suite immediately after that fix (before the "Average" fix above added 9 more tests): 420 passed (was 413), 0 regressions. `ruff check src/valis_workstation/settings_keys.py tests/test_settings_keys.py`: 0 findings.

## 2026-09-18

### Fixed
- `MergeSlidesDialog`'s "Overlap handling: Last" option (how to resolve two different slides sharing the same channel name, e.g. two staining rounds both labeled "DAPI") was byte-for-byte identical to "First". `merge_registered_slides` (`services/merge_slides.py`) mapped both to the same `Valis.warp_and_merge_slides(drop_duplicates=True)` call — which always keeps whichever occurrence comes first in slide order — despite the code's own log message claiming `"'last' handling will use reverse order"`. Nothing ever reordered or filtered anything for "Last"; selecting it always produced the exact same merge as "First", regardless of which slide's channel the user actually expected to win.

	Fixed with a new `_keep_last_occurrence()` helper: for "Last", it filters `selected_slides`/`channel_name_dict` *before* `src_f_list` is built, keeping only the last-occurring slide for each duplicate channel name (dropping the earlier duplicate(s) entirely) while leaving non-duplicate slides in their original relative order — the mirror image of what VALIS's own `drop_duplicates=True` already does for "First". Since duplicates are now resolved before VALIS ever sees the list, `drop_duplicates=False` is passed for "Last" (there's nothing left for VALIS itself to drop).

### Testing
- New `tests/test_merge_slides_service.py::TestKeepLastOccurrence` (4 tests) and `::TestMergeRegisteredSlidesLastDuplicateHandling` (3 tests): unit tests for the helper (no duplicates, a simple pair, a non-adjacent duplicate, a three-way duplicate) plus integration tests confirming "Last" keeps the later duplicate slide, "First" still keeps the earlier one, and the two now produce different `src_f_list`s for the same input (the regression this fix closes — before it, they were identical).
- All 7 fail to collect (`ImportError: cannot import name '_keep_last_occurrence'`) on the pre-fix tree (verified via `git stash` of just `services/merge_slides.py`, then restored).
- Full suite: `QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **413 passed** (was 406), 0 regressions.
- `ruff check src/valis_workstation/services/merge_slides.py tests/test_merge_slides_service.py`: 1 finding before and after (pre-existing `BLE001` on an unrelated line, confirmed via the same stash comparison), 0 new.

## 2026-09-16

### Fixed
- `MergeSlidesDialog`'s per-channel "Color" picker (Auto/Red/Green/Blue/Cyan/Magenta/Yellow/Gray/White, one combo box per channel row) had no effect on the saved output. `get_merge_config()` has always included each channel's chosen `"color"` in the dict it returned, but `services/merge_slides.py::merge_registered_slides` never read it — `Valis.warp_and_merge_slides` has a real `colormap` parameter for exactly this and it was never passed. Every merge used VALIS's own automatic per-channel colors regardless of what a user picked in the dialog, the same shape of bug already fixed for Save Options' format/pyramid choices (2026-09-08) and the "Normalize intensities" checkbox (2026-09-09).

	Fixed with a new `_resolve_channel_colormap()` helper in `services/merge_slides.py`:
	- Returns `None` (leave VALIS's own `colormap=slide_io.CMAP_AUTO` default untouched) when every channel is still on "Auto" — no equivalent-but-different override when the user didn't actually choose anything.
	- Otherwise builds a complete `{channel_name: (r, g, b)}` dict covering *every* configured channel — `Valis.warp_and_merge_slides` silently discards a dict-style colormap entirely if any expected channel name is missing from it, so a channel left on "Auto" within an otherwise-explicit set is filled in via VALIS's own automatic assignment (`valis.slide_io.get_colormap`, lazily imported like the existing normalize path already does), or white if that module can't be imported — never dropped.
	- `merge_registered_slides` passes the resolved dict as `merge_kwargs["colormap"]` only when non-`None`; it's forwarded on both the normal (`dst_f` set) and the normalize (`dst_f=None`, image built then saved separately) paths, since the colors are what gets embedded into the returned OME-XML either way.

### Testing
- New tests in `tests/test_merge_slides_service.py` (8 tests): unit tests for `_resolve_channel_colormap` (all-Auto, all-explicit without importing `slide_io`, mixed Auto+explicit via a fake `slide_io.get_colormap`, and the white fallback when `slide_io` can't be imported), plus integration tests for `merge_registered_slides` confirming an all-Auto config omits the `colormap` kwarg entirely and an explicit config reaches `registrar.warp_and_merge_slides` on both the normal and normalize paths.
- All 8 fail to collect (`ImportError: cannot import name '_resolve_channel_colormap'`) on the pre-fix tree (verified via `git stash` of just `services/merge_slides.py`).
- Full suite: `QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **402 passed** (was 394), 0 regressions.
- `ruff check src/valis_workstation/services/merge_slides.py tests/test_merge_slides_service.py`: all checks passed, 0 findings.

## 2026-09-16 (2)

### Fixed
- `MergeSlidesDialog`'s per-row "Include" checkbox and its "Select All"/"Select None" buttons had no effect on which slides were actually merged. `merge_registered_slides` (`services/merge_slides.py`) has always computed `selected_slides` (the slide names still checked in the dialog's table) but never used it — `merge_kwargs` never set `src_f_list`, so `Valis.warp_and_merge_slides` fell back to its own default of *every* slide in the registrar (`registrar.get_sorted_img_f_list()`) regardless of what was unchecked. Worse than a silently-ignored control: since `channel_name_dict` (built from only the checked rows) has no entry for an unchecked slide, and `warp_and_merge_slides` looks that entry up unconditionally for every slide it processes, unchecking even one slide would raise a bare `KeyError` from inside VALIS the moment a real merge reached it.

	Fixed by resolving each selected slide's source path via `registrar.slide_dict[name].src_f` and passing the result as an explicit `merge_kwargs["src_f_list"]` — on both the normal (`dst_f` set) and normalize (`dst_f=None`) paths, since it's a shallow copy of the same `merge_kwargs` dict either way. A selected name no longer present in the registrar raises a clear `UserVisibleError` before ever calling into VALIS, instead of a bare `KeyError` surfacing from inside it.

### Testing
- New `tests/test_merge_slides_service.py::TestMergeRegisteredSlidesSlideSelection` (4 tests): only checked slides reach `src_f_list` (and the excluded slide is absent from `channel_name_dict`); the all-checked case still passes an explicit `src_f_list` rather than relying on VALIS's default (so a future regression can't silently reintroduce the bug); a checked slide missing from the registrar raises `UserVisibleError` without calling `warp_and_merge_slides`; the normalize path's separate unsaved-build call also receives `src_f_list`.
- All 4 fail on the pre-fix tree (verified via `git stash` of just `services/merge_slides.py`, then restored) — 3 with `KeyError: 'src_f_list'`/`DID NOT RAISE`, matching the described defects exactly.
- Full suite: `QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **406 passed** (was 402), 0 regressions.
- `ruff check src/valis_workstation/services/merge_slides.py tests/test_merge_slides_service.py`: 1 finding before and after (pre-existing `BLE001` on an unrelated line, confirmed via the same stash comparison), 0 new.

## 2026-09-15

### Added
- `ui/high_contrast`/`ui/reduced_motion` settings keys, declared in `settings_keys.py` but fully dead (no reader/writer, no checkbox anywhere — a 2026-09-08 audit finding), are now a real accessibility feature.
	- `PreferencesDialog`'s User Interface tab gained two checkboxes: "High contrast mode" and "Reduce motion" (`src/valis_workstation/ui/dialogs/preferences_dialog.py`), following the same checkbox/load/save/restore-defaults pattern every other boolean field in that dialog already uses. Both default unchecked.
	- New `src/valis_workstation/utils/accessibility.py` is the one place that reads both settings back and applies their effect, re-read fresh on every call (no caching) so a Preferences change takes effect immediately — the same approach `app._ToolTipSuppressionFilter`/`performance._monitoring_enabled` already use.
	- High contrast: new `src/valis_workstation/styles/high_contrast_overrides.qss` (near-black/near-white text and backgrounds, a consistent 3px bright-yellow focus outline on every focusable widget class) is appended after the base theme when the setting is on. Applied at startup (`app.run_app`) and re-applied immediately from `MainWindow._on_preferences_changed` when it changes — no restart required.
	- Reduced motion: the two real `QPropertyAnimation` fade-outs in the app (`SplashScreen.finish`, `LoadingOverlay.dismiss`, `src/valis_workstation/ui/splash_screen.py`) now use `accessibility.reduced_motion_duration_ms(...)` instead of a bare literal duration, shortening 350ms/200ms fades to a near-instant 1ms when the setting is on.

### Testing
- New `tests/test_accessibility_settings.py` (30 tests) covering the settings readers, `compose_stylesheet`/`apply_theme`, both Preferences checkboxes' full save/reopen round trip, `MainWindow._on_preferences_changed`'s reapply call, and both splash-screen fade durations under the setting on/off.
- **27 of 30 fail on the pre-fix tree** (confirmed via `git stash` of the modified source files).
- Full suite: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -q` — **394 passed** (was 364), 0 regressions.
- `ruff check` on the four modified files: identical finding counts before/after (0 new); the two new files are clean.

## 2026-09-09

### Fixed
- `MergeSlidesDialog`'s "Normalize intensities" checkbox (checked by default, tooltip: "Normalize intensity ranges across channels. Recommended for better visualization.") had no effect on the saved output. `get_merge_config()` included `"normalize": self._normalize.isChecked()` in the dict it returned, but `services/merge_slides.py::merge_registered_slides` never read that key — it built `merge_kwargs` and called `registrar.warp_and_merge_slides(**merge_kwargs)` unconditionally, which has no `normalize` parameter of its own. Every merged multi-channel image was saved with each channel's raw, unstretched intensity range regardless of the checkbox.

	Fixed by branching on `merge_config["normalize"]` in `merge_registered_slides`:
	- **Off** (unchanged path): `registrar.warp_and_merge_slides(**merge_kwargs)` is called with `dst_f` set, exactly as before — VALIS builds, warps and saves the image in one call.
	- **On** (new path): `warp_and_merge_slides` is called with `dst_f=None` so it returns the built-but-unsaved `pyvips.Image` instead of writing it to disk. The new `_normalize_channels()` helper linearly stretches each band independently (its own observed min -> 0, its own observed max -> the pixel format's ceiling — 255 for `uchar`, 65535 for `ushort`; any other format, or an already-flat band, is left untouched rather than guessed at or divided by zero). The stretched image is then saved directly via `valis.slide_io.save_ome_tiff` (lazily imported, matching this codebase's existing `importlib.import_module("valis.registration")` pattern in `services/valis_pipeline.py`, since the full VALIS/pyvips stack isn't always installed), using the same tile size/compression/quality/pyramid options the non-normalize path would have used, falling back to `slide_io.get_tile_wh` off the registrar's reference slide when no explicit tile size was configured.

### Testing
- New `tests/test_merge_slides_service.py` (9 tests): unit tests for `_normalize_channels` against a lightweight fake mimicking the subset of the `pyvips.Image` API this module uses (band indexing, `min`/`max`, arithmetic, `cast`, `bandjoin` — real `pyvips`/VALIS aren't installed in this sandbox), plus integration tests for `merge_registered_slides` covering both branches (normalize on/off, explicit vs. computed tile size, mid-merge cancellation after the image is built but before it's saved, and progress-callback completion) — all mocking `registrar.warp_and_merge_slides` and `sys.modules["valis.slide_io"]`.
- All 9 tests **fail to collect (`ImportError`) on the pre-fix tree** (verified via `git stash` of just `services/merge_slides.py`).
- Full suite: `QT_QPA_PLATFORM=offscreen pytest tests/ -q` — **364 passed** (was 355), 0 regressions, in a lightweight environment (PySide6/pytest-qt/pandas/matplotlib/numpy/psutil; the full `uv sync` VALIS scientific stack, including `torch`/`pyvips`, was not installed — none of the touched code or its tests require it, by design).
- `ruff check src/valis_workstation/services/merge_slides.py tests/test_merge_slides_service.py`: all checks passed, 0 findings.

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

## 2026-04-11

### Added
- Main window modularization helpers:
	- `src/valis_workstation/ui/main_window_actions.py`
	- `src/valis_workstation/ui/main_window_documents.py`
	- `src/valis_workstation/ui/main_window_workflow.py`
- Global non-interactive UI test fixture in `tests/conftest.py` to prevent blocking dialogs during automated runs.
- Dedicated non-interactive regression checks in `tests/test_non_interactive_ui.py`.

### Changed
- `src/valis_workstation/main_window.py` now delegates menu/action wiring, document handlers, and registration workflow orchestration to dedicated modules.
- README architecture and roadmap updated to reflect current implementation status.

### Fixed
- Corrected stale documentation links that referenced removed `USER_MANUAL.md`.
- Corrected roadmap status for registration cancellation (implemented).

### Testing
- Full automated suite (no manual clicking required): `320 passed`.

### Notes
- Upstream VALIS parity audit completed against `MathOnco/valis` `v1.2.0`; local bundled `valis/` is aligned at audit time.

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
