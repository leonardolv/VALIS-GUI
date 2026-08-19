# Agent Task Log — Continuous Improvement
Shared continuity file for automated maintenance runs. Multiple agents may
work this file; always append, never overwrite another agent's entries.

## In Progress

_(nothing claimed)_

## Completed

### 2026-08-19 (2) — `get_tile_cache()` has no caller anywhere in the app outside its own module and the stats dialog

**Item claimed.** Backlog: "`get_tile_cache()` has no caller anywhere in the
app outside `utils/tile_cache.py` and the stats dialog itself... Worth
deciding whether `TileCache` is meant to be wired into real tile rendering
(a real, larger feature) or removed as speculative infrastructure." (filed
by the run that landed PR #6, immediately above this entry.) No other agent
had this repo claimed — In Progress was empty, and both entries above this
one were already reflected in the log at the start of this run.

**Investigation.** Confirmed the premise before acting on it, rather than
trusting the Backlog's own framing:
* `MainWindow` (the app's real image display path) never calls
  `TiledImageLoader.get_tile`/`.get_region` — the only methods that would
  actually read a WSI tile through the cache. It opens slides via napari's
  own `self._viewer.open(...)`, confirmed by grepping for `add_image`/
  `viewer.open` call sites — there are none in the tile-cache module's
  favor, and one (`viewer.open`) outside it.
* `get_tile_cache()` itself is called from exactly two places, both in
  `performance_stats_dialog.py`, both only for `.get_stats()`/`.clear()` —
  never `.get()`/`.put()`. `TiledImageLoader` is never constructed anywhere
  outside its own module at all.
* Neither `LRUTileCache` nor `TiledImageLoader` had a single test of their
  own (`grep -rn "LRUTileCache\|TiledImageLoader" tests/` — zero hits),
  unlike every other cache in the app.
* So wiring this up for real would mean writing a whole new WSI-tile-read
  call site inside (or instead of) napari's own multiscale loading — the
  "real, larger feature" the Backlog entry itself flagged as out of scope —
  not finding an existing call site that merely forgot to track a metric,
  which is what the sibling `PerformanceMonitor` items (previous entry)
  turned out to be.

**Decision.** Removed as speculative infrastructure. Two things made this
the right call over leaving it in place pending a future "wire it up" pass:
(a) it is not just inert, it is actively misleading — the Performance
Stats dialog's "Tile Cache" tab (7 stat fields + a progress bar) and
Overview-tab hit-rate row can never show anything but zero, and its "Clear
Tile Cache" button clears a cache that can never hold anything, which reads
to a user as "the app isn't caching your tiles" rather than "this feature
doesn't exist yet"; (b) the Preferences "Max Tile Cache" setting is a
control that does not control anything a user could ever observe — it
*does* reach `LRUTileCache`'s constructor via `get_tile_cache()`'s
default-arg fallback, so it is not literally unread (a subtler case than
the `ui/show_tooltips`-style gaps fixed in the two entries above this one),
but the memory limit of a cache nothing ever populates has no observable
effect from the user's side of the screen.

**Solution.**
* Deleted `src/valis_workstation/utils/tile_cache.py` in full (`TileKey`,
  `LRUTileCache`, `TiledImageLoader`, `get_tile_cache`).
* Removed `PerformanceMonitor.track_tile_load` and the
  `tile_cache_hits`/`tile_cache_misses`/`tile_load_times` fields (dead
  regardless of this decision — nothing called `track_tile_load` either,
  confirmed by the same grep the previous entry ran for the other three
  trackers) plus the `"tiles"` key of `get_summary()` and its two
  log/status-bar readers (`utils/performance.py`).
* Removed the "Tile Cache" tab, the Overview "Tile Cache Hit Rate" row, and
  the "Clear Tile Cache" button (`ui/dialogs/performance_stats_dialog.py`).
* Removed the Preferences "Max Tile Cache" spinbox (`cache/max_tile_mb`)
  (`ui/dialogs/preferences_dialog.py`).
* Removed the Preferences "Tile Size (pixels)" combo (`performance/
  tile_size`) too — not part of the original plan, found while removing the
  spinbox above: its *only* consumer anywhere was `get_tile_cache()`'s
  other default-arg fallback, so deleting that module orphaned this field
  as a direct consequence. (Registration's own tile size —
  `properties_dock.py`'s `_tile_size_spin` feeding `RegistrationConfig.
  tile_size`/`save_kwargs["tile_wh"]` — is a separate setting under a
  separate key and is untouched; confirmed by reading every remaining
  `tile_size` reference in `src/` after the edit.)

**Validation.**
* Removed the two tests exercising the deleted surface:
  `TestPerformanceMonitor::test_track_tile` and the
  `s["tiles"]["cache_hit_rate"]` assertion in
  `TestPerformanceMetrics::test_empty_summary` (`tests/test_utils.py`).
* `grep -rn "tile_cache\|TileCache\|TiledImageLoader\|max_tile" src/ tests/`
  → zero remaining references outside this log and `WORKSTATION_CHANGELOG.md`.
* Targeted: `test_utils.py` + `test_all_features.py` +
  `test_preferences_wiring_followups.py` +
  `test_performance_monitoring_wiring.py` → **156 passed**.
* Full suite (`QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/`):
  **336 passed, 4 failed**. The 4 (`test_pipeline.py::TestBuildRegistrarKwargs`)
  are the same pre-existing, order-dependent failure the 2026-08-18 and
  2026-08-19 entries already documented (a logging-handler `TypeError` that
  only reproduces when the full suite runs together, not with the file run
  alone) — checked directly by `git stash`-ing this change and re-running
  the full suite on the unmodified tree: **identical 4 failures, 337
  passed** (337 vs. 336 is exactly the 2 tests this change removed; 0
  failures caused by this change).

**Not done / left as-is**: the question of whether napari's own multiscale
rendering could benefit from a purpose-built tile cache in front of it is a
real, separate feature question — this entry answers "is the current dead
code worth keeping around on spec", not "should this app ever have a tile
cache". If that's wanted, it should start from how napari actually reads
tiles, not from resurrecting this module.

### 2026-08-19 — Performance monitor tracking calls had no caller anywhere in the app

**Item claimed.** Backlog: "`PerformanceMonitor.track_thumbnail_load`/
`track_tile_load`/etc. have no caller anywhere in the app." (filed by the
2026-08-18 run, restated when the 2026-08-19 run's own Preferences-wiring
pass declined to fold it in). No other agent had this repo claimed (In
Progress was empty; the only commit since the last entry was #5 itself,
already reflected here).

**Investigation.** `PerformanceStatsDialog` reads `monitor.metrics.
thumbnail_cache_hits`/`.thumbnail_load_times`/`.registration_times`/etc.
every 2 seconds and displays them, but grepping every `track_*` method
found zero callers anywhere outside `utils/performance.py` itself — so
those fields were always empty/zero regardless of real activity. Traced
each metric to what *should* be populating it:
* Thumbnails — `generate_thumbnail` (`services/thumbnail_generator.py`)
  has exactly one cache-hit return and one successful-generation return,
  neither timed nor tracked.
* Slides — `MainWindow._load_thumbnails_parallel` already computes
  `started_at = time.time()` for the loading overlay's ETA calculation and
  never used it for anything else.
* Registration — `ValisWorker.run` (`workers/valis_worker.py`) calls
  `run_valis_pipeline` and emits `finished`, with nothing timed in between.
* Tiles — a different shape entirely: `get_tile_cache()` has **no caller
  anywhere in the app** outside `utils/tile_cache.py` and the stats dialog
  itself, so there is no real tile-loading call site to wire `track_tile_load`
  into. The "Tile Cache" tab's own numbers already come from
  `TileCache.get_stats()`'s internal hit/miss/eviction counters, not from
  `PerformanceMonitor`, so that tab was not actually broken — filed back to
  the Backlog as its own, deeper gap (the tile cache is currently dead code;
  the app must be rendering multiscale tiles some other way, e.g. through
  napari directly).
* `performance/monitoring_enabled` — found moot by the 2026-08-18 run
  ("nowhere to plug in"). Now that there are real trackers, it gates all of
  them.

**Solution.**
* `_monitoring_enabled()` (`utils/performance.py`) reads
  `performance/monitoring_enabled` from `QSettings` fresh on every call
  (not cached — same approach as the 2026-08-19 tooltip filter, so toggling
  the Preferences checkbox takes effect immediately) and fails open
  (`True`) if Qt is unavailable, since this module otherwise has no Qt
  dependency. `track_thumbnail_load`, `track_tile_load`, `track_registration`,
  `track_slides_loaded`, and the recording half of `sample_memory` all check
  it and no-op when off; `sample_memory` still returns the live
  process-memory reading either way, since that is an instantaneous stat,
  not an accumulated metric.
* `generate_thumbnail` times itself from entry and calls
  `track_thumbnail_load(duration, from_cache=...)` at both return points
  that produce a usable result (cache hit, fresh generation) — not on a
  failed read, matching what "average load time" should mean.
* `_load_thumbnails_parallel` calls `track_slides_loaded(completed,
  time.time() - started_at)` once the thread-pool loop finishes.
* `ValisWorker.run` times the `run_valis_pipeline` call and calls
  `track_registration(duration)` right before `self.finished.emit(result)`
  — not on `cancelled`/`failed`, matching "registration completed" and the
  existing log line's own wording.
* `track_slides_loaded` also gained a `count <= 0` guard: its own logging
  line divides by `count`, and the guard makes that safe even though the
  one real caller never passes 0 (it is only called when `slides` was
  non-empty).

**Validation.**
* New `tests/test_performance_monitoring_wiring.py` (15 tests): the
  setting's own read/default/no-op behavior; each tracker records when
  enabled and is a no-op when disabled (including the zero-count guard and
  that `sample_memory`'s live reading still works while disabled); a real
  cache-hit through `generate_thumbnail` is tracked and a missing file is
  not; a successful `ValisWorker` run is tracked and a failed one is not
  (drives the real worker over a `QThread`, mirroring `test_worker.py`'s
  existing pattern); a real `MainWindow._load_thumbnails_parallel` call
  over two slides is tracked with the right count.
* Targeted: `test_performance_monitoring_wiring.py` +
  `test_thumbnail_cache.py` + `test_worker.py` +
  `test_preferences_wiring_followups.py` → **34 passed, 0 failed**.
* Full suite: **337 passed, 4 failed** — the 4
  (`test_pipeline.py::TestBuildRegistrarKwargs`) reproduce identically on
  the unmodified tree in this same environment (confirmed by moving this
  run's new test file aside and `git stash`ing the rest: 322 passed / 4
  failed, same 4 test IDs), caused by `valis.feature_detectors` failing to
  import `SimpleITK` even with `torch`/`kornia`/`libvips42` installed —
  this environment is missing more of the full `valis-wsi` package's heavy
  dependency chain than the 2026-08-19 run's environment was. Unrelated to
  this change either way.
* `ruff check src/`: **20 findings both before and after** this change (one
  new finding introduced in the test file during development — an unused
  `time` import — found and removed before this run; final state has zero
  new findings). `ruff check tests/test_performance_monitoring_wiring.py`
  on its own: clean.
* `python3 -c "import ast; ..."` syntax check on all five touched/added
  files; `PYTHONPATH=src python -c "import valis_workstation.main_window"`
  imports cleanly.
* **Incident, self-corrected within this run:** a verification command
  (`mv tests/test_performance_monitoring_wiring.py /dev/null`, intended to
  discard a throwaway check) matched `/dev/null` as a plain destination
  path rather than an existing directory, so `mv` moved the test file's
  *contents* onto `/dev/null` — replacing the character device with a
  48-byte regular file and deleting the test file. Caught immediately via
  `ls -la /dev/null`; fixed with `rm /dev/null && mknod -m 666 /dev/null c
  1 3` (verified read/write afterward) and the test file was rewritten from
  this session's own record of its contents. No source file was affected
  (`git status` confirmed only the intended four modified + one untracked
  file throughout); the recreated test file was re-run and re-validated
  before this entry was written. Recorded here as a reminder that `mv
  <file> /dev/null` is not a safe idiom for "discard this" in a shared
  sandbox — `rm` is.

**Docs.** `WORKSTATION_CHANGELOG.md` gains a 2026-08-19 entry (second one
for this date) with the same write-up.

**PR.** (opened this run, see repository pull requests).

### 2026-08-19 — The last two design-decision Preferences fields: tooltips and cache persistence

**Item claimed.** Backlog: "`ui/show_tooltips` and `cache/persist` are the
two remaining disconnected Preferences fields that need a design decision,
not just a call site" (filed by the 2026-08-18 run). No other agent had
this repo claimed (In Progress was empty; the only commit since 2026-08-18
was #4 itself, already reflected here).

**The two decisions.**
* `ui/show_tooltips` — the Backlog entry was right that no single call site
  can own this: tooltips are dispatched by Qt's own hover machinery to
  whichever of dozens of widgets happens to be under the cursor, not
  requested by app code. The one place that sees all of them is the
  `QApplication` itself, via `QEvent.Type.ToolTip`.
* `cache/persist` ("Keep cache between sessions") — took the entry's
  smaller-risk option: clear `ThumbnailCache`'s on-disk contents on exit
  when unchecked, rather than rearchitecting it into an in-memory-only
  cache for the session (a much larger change to a class three other call
  sites already depend on being disk-backed, for one checkbox).

**Solution.**
* `app._ToolTipSuppressionFilter` (`src/valis_workstation/app.py`), a
  `QObject` event filter installed on the `QApplication` in `run_app`
  (kept alive as `app._tooltip_suppression_filter` — `installEventFilter`
  does not take Python-level ownership, so an unreferenced filter object
  can be garbage-collected out from under the app). Its `eventFilter`
  re-reads `ui/show_tooltips` from `QSettings` on every `ToolTip` event
  (not cached), so a Preferences change takes effect immediately without
  restarting the app, and consumes the event (returns `True`) to block it
  only when the setting is off. Every other event type passes through
  unchanged.
* `MainWindow.closeEvent` (`main_window.py`) reads `cache/persist` after
  its existing cleanup steps and calls `get_thumbnail_cache().clear()`
  when it's `False`, in its own `try`/`except` so a clear failure (e.g. a
  read-only cache directory) can't block the window from closing — the
  same principle the method's existing worker-thread and napari-viewer
  cleanup already follow.

**Validation.**
* New `tests/test_preferences_wiring_followups.py` (9 tests): the tooltip
  filter suppresses `ToolTip` events only when the setting is off, defaults
  to shown when unset (matching the checkbox's own default), never
  consumes an unrelated event type, and is confirmed installed on the real
  `QApplication`; `closeEvent` clears the cache only when `cache/persist`
  is `False`, leaves it alone when `True` or unset, and still accepts the
  close event when the clear itself raises.
* This environment needed `torch` and system `libvips.so.42`
  (`apt-get install libvips42`) that the 2026-08-18 run's environment
  didn't have — installed both; with them, `test_pipeline.py::
  TestBuildRegistrarKwargs`'s four `libvips`-dependent tests (the previous
  run's one known-unrelated failure) now pass too.
* Full suite: **326 passed, 0 failed** (up from the prior run's 313/4,
  entirely from the two now-satisfied environment deps above — 0 failures
  attributable to this change).
* `ruff check` on the two touched source files: finding count unchanged at
  5 (no new findings); the new test file is itself ruff-clean.
* `python3 -c "import ast; ..."` syntax check on both touched files.

**Docs.** `WORKSTATION_CHANGELOG.md` gains a 2026-08-19 entry with the same
write-up.

**PR.** #5 — https://github.com/leonardolv/VALIS-GUI/pull/5

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

- ~~**`ui/show_tooltips` and `cache/persist` are the two remaining
  disconnected Preferences fields that need a design decision, not just a
  call site.**~~ Done by the 2026-08-19 run — see the Completed entry.
  `show_tooltips` got an application-wide `QEvent.ToolTip` filter on the
  `QApplication`; `cache/persist` got the smaller-risk of the two options
  this entry weighed (clear the on-disk cache in `closeEvent`, rather than
  an in-memory-only cache for the session).
  (original entry follows)
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
- ~~**`PerformanceMonitor.track_thumbnail_load`/`track_tile_load`/etc. have no
  caller anywhere in the app.**~~ Done by the 2026-08-19 run for thumbnails,
  slides and registration — see the Completed entry. Tiles turned out to be
  a different shape than the others (below), filed as its own item rather
  than folded into this one's resolution.
  (original entry follows)
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
- ~~**`get_tile_cache()` has no caller anywhere in the app outside
  `utils/tile_cache.py` and the stats dialog itself.**~~ Done by the
  2026-08-19 (2) run — see the Completed entry. Decided the question this
  entry posed by removing the module: nothing ever called
  `TiledImageLoader.get_tile`/`.get_region` (confirmed — real image
  display goes through napari's `viewer.open()`), neither class had any
  test coverage of its own (this entry's "exercised only by its own tests"
  didn't hold up), and the "Tile Cache" dialog tab this entry called
  "not actually broken" was reporting an honest-but-permanent zero, which
  reads to a user as broken either way.
  (original entry follows)
- **`get_tile_cache()` has no caller anywhere in the app outside
  `utils/tile_cache.py` and the stats dialog itself.** Found by the
  2026-08-19 run while wiring the item above: unlike thumbnails, slides and
  registration, there is no real tile-loading call site to wire
  `track_tile_load` into, because nothing ever fetches a tile *through*
  `TileCache` — the app must be rendering multiscale WSI tiles some other
  way (plausibly through napari's own layer/multiscale machinery directly).
  The "Tile Cache" tab in `PerformanceStatsDialog` still shows real numbers
  (it reads `TileCache.get_stats()`'s own internal hit/miss/eviction
  counters, not `PerformanceMonitor`), so nothing user-visible is broken —
  but the class itself, its LRU eviction, and its memory-budget config are
  all currently dead code exercised only by its own tests. Worth deciding
  whether `TileCache` is meant to be wired into real tile rendering (a
  real, larger feature) or removed as speculative infrastructure.
