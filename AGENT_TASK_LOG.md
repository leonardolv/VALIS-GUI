# Agent Task Log — Continuous Improvement
Shared continuity file for automated maintenance runs. Multiple agents may
work this file; always append, never overwrite another agent's entries.

## In Progress

_(nothing claimed)_

## Completed

### 2026-08-18 — The Preferences dialog persisted 13 settings; nothing ever read 7 of them back

**First run against this repo** — `AGENT_TASK_LOG.md` did not exist, created per
this task's template. No prior claims to check.

**Investigation.** Surveyed the codebase for a bounded, verifiable bug (an
Explore agent pass, then read directly): `WORKSTATION_CHANGELOG.md`'s own
"Notes" section already flags one instance of this app's recurring shape
("Comparison modes in Blink viewer are practical UI-level modes... future
iterations can deepen semantic rendering behavior") — a control that's
visually present and self-consistent but not fully plumbed into real
behavior. `PreferencesDialog` (`src/valis_workstation/ui/dialogs/
preferences_dialog.py`) turned out to be the same shape at a larger scale:
it persists 13 fields to `QSettings` on save, and grepping every one of
those keys (`cache/directory`, `performance/parallel_workers`,
`ui/recent_files_count`, etc.) across `src/` found none read anywhere
outside the dialog itself. `_on_preferences_changed` shows "Some preference
changes require restarting the application to take effect" on every save —
true of nothing, since no restart made any of them take effect either.

**Root cause, concretely, for each of the 7 fixed:**
* `performance/parallel_workers` — `_load_thumbnails_parallel` hardcoded
  `max_workers = min(4, total_slides)`.
* `ui/recent_files_count` — `_add_to_recent_folders` hardcoded `recent[:10]`.
* `ui/confirm_close` — the checkbox existed; `closeEvent` had no
  confirmation prompt of any kind behind it.
* `ui/show_statusbar` — `_setup_status_bar` always left the bar visible.
* `cache/directory` / `cache/max_thumbnail_mb` — `get_thumbnail_cache()`'s
  lazy singleton always called `ThumbnailCache()` with zero arguments,
  so the constructor's own defaults (`~/.valis_cache`, 500 MB) won regardless
  of what the dialog said.
* `cache/max_tile_mb` / `performance/tile_size` — identical shape one layer
  down, `get_tile_cache()`, called with no arguments from both its call
  sites (`performance_stats_dialog.py`).
* `ui/default_thumbnail_size` — `generate_thumbnail(slide_path, max_size=512)`
  was a literal in `_load_thumbnails_parallel`.

**Solution.** Read the relevant `QSettings` key at each real call site
(`main_window.py`, `thumbnail_cache.py`, `tile_cache.py`,
`performance_stats_dialog.py`), falling back to the same defaults the
dialog itself uses. `get_tile_cache(max_memory_mb=None, tile_size=None)`
changed its defaults from literals to `None`-sentinels resolved from
`QSettings` inside the function, preserving its documented "only used on
first call" lazy-singleton contract for any caller that does pass explicit
values.

**Deliberately not fixed, filed to Backlog:** `ui/show_tooltips` (needs an
application-wide `QEvent.ToolTip` event filter, not a single call site —
different shape of fix than the other twelve), `cache/persist` (a real
behavior decision — clear the cache on exit when unchecked — not a wiring
gap), and `performance/monitoring_enabled` — found to be moot while
investigating: `PerformanceMonitor.track_thumbnail_load` and its siblings
(`utils/performance.py`) have **no caller anywhere in the app**, so the
Performance Statistics dialog's hit/miss/load-time metrics are always empty
regardless of the toggle. That's a separate, deeper gap (instrumentation
never wired to the operations it's meant to measure) worth its own pass
rather than folding into this one.

**Validation.**
* This sandbox's `xvfb-run` aborts on a bare `QApplication()` construction
  — confirmed on a clean tree with this change's files stashed, so it is a
  pre-existing environment issue, not a regression. `QT_API=pyside6
  QT_QPA_PLATFORM=offscreen pytest` (no `xvfb` needed) sidesteps it.
* Targeted subset (`test_thumbnail_cache.py`, `test_app.py`,
  `test_gui_components.py`, `test_all_features.py`): **153 passed, 0
  failed**.
* Full suite: **313 passed, 4 failed** — the 4 (`test_pipeline.py::
  TestBuildRegistrarKwargs`) reproduce identically with this change's files
  stashed, caused by `torch` not being installed in this environment
  (`valis.feature_detectors not importable`), unrelated to this change.
* `python3 -c "import ast; ..."` syntax check on all four touched files;
  `python -c "import valis_workstation.main_window"` imports cleanly.

**Docs.** `WORKSTATION_CHANGELOG.md` gains a 2026-08-18 entry with the same
write-up, matching this repo's existing Added/Changed/Fixed/Testing
convention.

**PR.** #4 — https://github.com/leonardolv/VALIS-GUI/pull/4

## Backlog

- **`ui/show_tooltips` and `cache/persist` are the two remaining
  disconnected Preferences fields that need a design decision, not just a
  call site.** Filed by the 2026-08-18 run. `show_tooltips` needs an
  application-wide `QEvent.ToolTip` filter (or per-widget tooltip removal),
  a different shape of fix than the other twelve fields, which each had
  exactly one real call site already computing the value some other way.
  `cache/persist` ("Keep cache between sessions") needs a decision about
  what "not persisting" means operationally — clear `ThumbnailCache`'s disk
  contents in `closeEvent`? Never write to disk in the first place, keeping
  an in-memory-only cache for the session? — before it's a small fix rather
  than a modeling question.
- **`PerformanceMonitor.track_thumbnail_load`/`track_tile_load`/etc. have no
  caller anywhere in the app.** Filed by the 2026-08-18 run, found while
  investigating why `performance/monitoring_enabled` had nowhere to plug in.
  `PerformanceStatsDialog` reads `monitor.metrics.thumbnail_cache_hits` /
  `.thumbnail_load_times` / etc. and displays them, but nothing in
  `thumbnail_generator.py`, `tile_cache.py`, or anywhere else ever calls the
  tracking methods that would populate those fields — the dialog's own
  numbers are always zero/empty. This is a bigger question than the
  Preferences wiring above: it touches every operation the dialog claims to
  measure (thumbnail loads, tile loads, cache hits/misses, memory samples),
  so it's its own pass rather than a fold-in. Worth deciding whether the
  dialog is wanted at all before wiring a dozen call sites to feed it.
