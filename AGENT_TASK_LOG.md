# Agent Task Log — Continuous Improvement
Shared continuity file for automated maintenance runs. Multiple agents may
work this file; always append, never overwrite another agent's entries.

## In Progress

_(nothing claimed)_


## Completed

### 2026-09-16 (3) UTC — `MergeSlidesDialog`'s "Include" checkbox / Select All/None are discarded by the merge service
Branch `claude/eager-brown-06xj0c` · PR
[#15](https://github.com/leonardolv/VALIS-GUI/pull/15) · Status: **done, merged**

**Claimed** after a fresh code audit — the Backlog was fully exhausted
(every entry struck through, referencing a real Completed entry), and
`list_pull_requests` for this branch came back empty (learned from the
2026-09-16 (1) collision entry above: check open PRs, not just the log).

**Root cause.** `merge_registered_slides` (`services/merge_slides.py`)
builds `channel_name_dict` and `selected_slides` from only the rows still
checked in `MergeSlidesDialog`'s "Include" column (also driven by its
"Select All"/"Select None" buttons) — but `selected_slides` was then never
read again anywhere in the file (confirmed by grep before touching
anything). `merge_kwargs` never set `src_f_list`, so
`Valis.warp_and_merge_slides` (`valis/registration.py`) fell back to its
own default, `self.get_sorted_img_f_list()` — *every* slide registered in
the `Valis` object, regardless of what the dialog's checkboxes said. This
is worse than a silently-ignored control: `warp_and_merge_slides` looks up
`channel_name_dict_by_name[slide_obj.name]` unconditionally for every
slide in `src_f_list`, and an unchecked slide has no entry there (it was
never added to `channel_name_dict`) — so unchecking even one slide and
running a real merge would raise a bare `KeyError` from inside VALIS
rather than just merging the "wrong" (i.e. every) slide. Same "real
control, silently discarded" shape as the Save Options format/pyramid bug
(#9), the Normalize checkbox (#10), and the per-channel Color picker
(#14) already fixed in this log — found by re-reading this exact
function while re-verifying #14's fix, not by a new audit angle.

**Solution.** Resolve each selected slide's real source path via
`registrar.slide_dict[name].src_f` (the same attribute `_export_roi_crop`
in `main_window.py` already reads off registrar slide objects) right
after `selected_slides` is built, and pass the result as an explicit
`merge_kwargs["src_f_list"]` — forwarded on both the normal (`dst_f` set)
and normalize (`dst_f=None`, built-then-saved-separately) paths, since the
normalize path's `unsaved_kwargs = dict(merge_kwargs)` copies it forward
automatically. A checked slide name no longer present in
`registrar.slide_dict` (defensive — shouldn't happen in practice, since
the names originate from the same registrar) now raises a clear
`UserVisibleError` naming the missing slide, instead of a bare `KeyError`
surfacing from inside VALIS's own merge code. Deliberately passes
`src_f_list` explicitly even when every slide is checked, rather than
only when a subset is selected — relying on VALIS's own default for the
"nothing deselected" case would leave the exact same bug latent for the
next slide anyone actually unchecks.

**Validation.**
* New `tests/test_merge_slides_service.py::TestMergeRegisteredSlidesSlideSelection`
  (4 tests): only checked slides reach `src_f_list` in the right order,
  and the excluded slide has no entry in `channel_name_dict`; the
  all-checked case still asserts an explicit `src_f_list` (so a future
  regression reintroducing reliance on VALIS's default fails loudly); a
  checked slide missing from the registrar raises `UserVisibleError`
  without ever calling `registrar.warp_and_merge_slides`; the normalize
  path's separate unsaved-build call also receives `src_f_list`.
* All 4 **fail on the pre-fix tree** (`git stash` of just
  `services/merge_slides.py`, rerun, then restored) — `KeyError:
  'src_f_list'` for three of them and `DID NOT RAISE UserVisibleError`
  for the fourth, matching the two described defects exactly.
* Full suite: `QT_API=pyside6 QT_QPA_PLATFORM=offscreen pytest tests/ -q`
  → **406 passed** (was 402 pre-fix, confirmed on the same stashed tree),
  0 regressions.
* `ruff check src/valis_workstation/services/merge_slides.py
  tests/test_merge_slides_service.py`: 1 finding before and after
  (pre-existing `BLE001` on an unrelated line, confirmed via the same
  stash comparison — 0 new).
* Environment: reused this repo's established lightweight-venv approach
  (`/home/user/.venvs/valis-gui`: PySide6, pytest, pytest-qt, numpy,
  psutil, pandas, matplotlib, ruff — built fresh this run, plus
  `apt-get install libegl1 libgl1 libglx-mesa0` for PySide6's `QtGui`
  import under `QT_QPA_PLATFORM=offscreen`); the full VALIS scientific
  stack (torch/pyvips/kornia/...) was not needed, since the touched code
  path is exercised via a mocked `registrar` and the tests never import
  real `pyvips`/`valis.slide_io`.
* `WORKSTATION_CHANGELOG.md` gains a matching `2026-09-16 (2)` entry.

**PR.** [#15](https://github.com/leonardolv/VALIS-GUI/pull/15).

### 2026-09-16 (2) UTC — `MergeSlidesDialog`'s per-channel "Color" picker is discarded
Branch `claude/blissful-clarke-01nad7` · PR
[#14](https://github.com/leonardolv/VALIS-GUI/pull/14) · Status: **done, merged**
(this repo's GitHub Actions runs never actually fire — confirmed via the
Actions API showing 0 workflow runs ever, including on already-merged PR
#11 — so merged on local validation per this file's own established
precedent, not on a green CI check.)

**Claimed** after re-reading the Backlog and confirming it is genuinely
fully resolved (every entry struck through, referencing a real Completed
entry) — no unclaimed item existed, so this run did a fresh audit rather
than a Backlog carry-over, per the task's fallback instruction. Also
checked `gh`/`list_pull_requests` for open PRs first (learned from the
2026-09-16 (1) collision entry above) — none open.

**Root cause.** `MergeSlidesDialog` (`ui/dialogs/merge_slides_dialog.py`)
gives every channel row a "Color" combo box (Auto/Red/Green/Blue/Cyan/
Magenta/Yellow/Gray/White) and includes the chosen value in
`get_merge_config()["channels"][i]["color"]`. `merge_registered_slides`
(`services/merge_slides.py`) reads `slide_name`/`channel_name` off each
entry to build `channel_name_dict` but never reads `"color"` anywhere —
confirmed by grep (`color` appeared only in the function's own docstring
before this fix). `Valis.warp_and_merge_slides` (`valis/registration.py`)
has a real `colormap` parameter documented as "List of RGB colors (0-255)
to use for channel colors," defaulting to `slide_io.CMAP_AUTO`
("auto-assign") — never passed. Net effect: every merged multi-channel
image got VALIS's own automatically-assigned channel colors regardless of
what a user picked, the same "real control, silently discarded" shape as
the Save Options format/pyramid bug (#9) and the Normalize checkbox bug
(#10) already fixed in this log.

**Solution.** New `_resolve_channel_colormap(channels)` in
`services/merge_slides.py`:
- Maps the 8 named colors to RGB triples (a plain module-level dict,
  `_NAMED_CHANNEL_COLORS` — "Auto" is deliberately not a key).
- Returns `None` when every channel is still "Auto" — `merge_kwargs`
  then omits the `colormap` key entirely, leaving VALIS's own
  `CMAP_AUTO` default untouched rather than passing an
  equivalent-but-different override (and, more importantly, not forcing
  every existing all-Auto test/config down a new code path).
- Otherwise builds a **complete** `{channel_name: (r, g, b)}` dict
  covering every configured channel, not just the explicitly-colored
  ones — read `valis/slide_io.py::check_colormap`'s dict branch directly
  before writing this: a dict-style colormap missing even one expected
  channel name is rejected wholesale (falls back to no colors at all,
  silently, via a `print_warning`), so a partial dict would have
  silently dropped the colors the user *did* pick the moment any other
  channel was left on "Auto." Channels left "Auto" within an
  otherwise-explicit set are filled in via VALIS's own automatic
  assignment (`valis.slide_io.get_colormap`, lazily imported — matches
  the existing normalize path's `importlib.import_module` pattern, since
  `slide_io` transitively imports `torch`/`kornia`/`jpype` and this
  module is otherwise import-light), falling back to white with a
  logged warning if that import fails, so a missing/broken VALIS install
  degrades gracefully instead of losing the user's explicit choices too.
- `merge_registered_slides` sets `merge_kwargs["colormap"]` only when
  the resolved value isn't `None`, and — checked directly, since it
  matters — the normalize path's separate `dst_f=None` build call
  inherits it via `dict(merge_kwargs)` before that key is stripped, so
  the colors reach the OME-XML VALIS returns (`create_ome_xml` embeds
  `colormap` regardless of whether `dst_f` is set) even on the
  normalize-then-save-via-`slide_io` path where VALIS itself never
  writes the file.

**Why not "remove the checkbox" instead:** established precedent in this
log (#9, #10) is to implement a real, well-specified control rather than
delete it when the underlying library already supports it — `colormap`
here is a first-class, documented `Valis.warp_and_merge_slides` parameter,
not a made-up behavior.

**Validation.**
* New tests in `tests/test_merge_slides_service.py` (8 tests):
  `_resolve_channel_colormap` unit tests (all-Auto → `None`; all-explicit
  builds the dict **without** importing `valis.slide_io` at all — asserted
  by deleting it from `sys.modules` first and confirming no `ImportError`;
  mixed Auto+explicit calls a mocked `slide_io.get_colormap` for only the
  Auto names and merges the result with the explicit ones; the white
  fallback + logged warning when `slide_io` can't be imported; an unknown
  color string treated as "Auto" rather than raising) plus
  `merge_registered_slides` integration tests (all-Auto omits the
  `colormap` kwarg entirely; explicit colors reach
  `registrar.warp_and_merge_slides` on both the plain-save path and the
  normalize path's separate unsaved-build call).
* All 8 **fail to collect** (`ImportError: cannot import name
  '_resolve_channel_colormap'`) on the pre-fix tree — confirmed via
  `git stash` of just `services/merge_slides.py`, rerun, then restored.
* Full suite: `QT_QPA_PLATFORM=offscreen pytest tests/ -q` →
  **402 passed** (was 394 pre-fix, confirmed on the same stashed tree), 0
  regressions.
* `ruff check src/valis_workstation/services/merge_slides.py
  tests/test_merge_slides_service.py`: all checks passed, 0 findings
  (both before writing the new code and after).
* Environment: this sandbox had no existing VALIS-GUI venv, so a fresh
  lightweight one was built at `/home/user/.venvs/valis-gui`
  (PySide6, pytest, pytest-qt, numpy, psutil, pandas, matplotlib) — same
  minimal-dependency approach documented by every prior entry in this log;
  the full `uv sync` VALIS scientific stack (torch/pyvips/kornia/...) was
  not needed, since the touched code lazily imports `valis.slide_io` and
  the tests mock it out.
* `WORKSTATION_CHANGELOG.md` gains a matching 2026-09-16 entry.

**PR.** [#14](https://github.com/leonardolv/VALIS-GUI/pull/14).

### 2026-09-16 UTC — Duplicate-claim collision on the `ui/high_contrast`/`ui/reduced_motion` item (process note, no code change)
Branch `claude/loving-feynman-qjb06m` · PR: see below · Status: **done**

**What happened.** This run read `AGENT_TASK_LOG.md` on `main` at start,
saw "nothing claimed" In Progress and only one open Backlog item
(`PerformanceMonitor.track_tile_load`, already deferred as a bigger
architectural call), and independently built the exact same fix the
2026-09-15 run above had already completed on its own branch
(`claude/loving-feynman-4kgevh`, PR #11) — full checkboxes, live-applied
high-contrast QSS overlay, and a `BlinkViewerDialog` reduced-motion gate.
That run's own log update (the entry directly above this one) lived only
on its PR branch and had not yet been merged to `main`, so it was
invisible to this run's initial check — the collision-detection protocol
("check for another agent's in-progress work") only reads what's on the
branch you start from, and an unmerged completed PR on a *different*
branch is a real, unhandled gap in that protocol worth flagging for
whoever next revises it.

The collision surfaced only once this run pushed its own branch and
queried open PRs before creating a new one — PR #11 was sitting open
(still in draft) alongside this run's new PR #12, both targeting the
identical Backlog entry.

**Resolution, not a re-fix.** Compared both implementations: #11 is a
superset (it additionally wires `ui/reduced_motion` into the two real
`QPropertyAnimation` fades in `ui/splash_screen.py`, and factors the logic
into a dedicated, cleanly-documented `utils/accessibility.py` module,
versus this run's narrower `app.py`/`blink_viewer.py`-only version).
Checked out #11's branch into a worktree and independently ran its full
test suite (**394 passed**) and `ruff check` on its new/touched files
(0 findings) before trusting it. Marked #11 ready for review and merged it
(squash) rather than merging this run's own PR #12, which was closed as a
duplicate with a comment pointing at #11 and the validation performed.
This run's own branch/commit are otherwise unused.

**Takeaway for future runs:** before opening a PR, check
`gh pr list`/`list_pull_requests` for the target repo — not just the log
file — since a completed-but-unmerged PR from a concurrent or very recent
run is real in-progress work the log alone won't show if that run's log
update hasn't landed on `main` yet.

### 2026-09-15 UTC — `ui/high_contrast`/`ui/reduced_motion` settings keys were fully dead
Branch `claude/loving-feynman-4kgevh` · PR
[#11](https://github.com/leonardolv/VALIS-GUI/pull/11) · Status: **done**

**Claimed** from the Backlog entry filed by the 2026-09-08 audit
("scaffolding for an accessibility feature that was never wired up").
Unlike every other Preferences field this repo has fixed before
(`ui/show_tooltips`, `cache/persist`, the performance trackers — see the
2026-08-18/19 entries below), these two had **no UI entry point at all**:
`settings_keys.py` declared both, but a repo-wide grep found zero
readers/writers and no corresponding checkbox anywhere, including
`PreferencesDialog`. Wired up as a small real accessibility feature rather
than deleted, matching this repo's established preference for "wire it"
over "delete it" whenever the underlying feature is real user value.

**Root cause.** Pure scaffolding — the keys were declared and never
followed up with a checkbox or a reader, confirmed by grep before starting
rather than assumed.

**Solution.**
* `utils/accessibility.py` (new) is the one place that reads both settings
  back and applies their effect — mirroring `app._ToolTipSuppressionFilter`
  and `performance._monitoring_enabled`'s "re-read fresh on every call, no
  caching" shape, so a Preferences change takes effect immediately without
  restarting the app:
  * `high_contrast_enabled()` / `should_reduce_motion()` read the two
    QSettings keys, default `False`.
  * `reduced_motion_duration_ms(normal_ms)` returns `normal_ms` normally,
    or a near-zero `REDUCED_MOTION_DURATION_MS` (1ms — positive rather than
    literal 0, so `QPropertyAnimation.finished` still fires asynchronously)
    when reduced motion is on.
  * `compose_stylesheet(base_css)` appends
    `styles/high_contrast_overrides.qss` (new — a real higher-contrast QSS
    variant: near-black/near-white text and backgrounds instead of the base
    theme's mid-grey palette, plus a 3px bright-yellow focus outline
    applied consistently across every focusable widget class, versus the
    base theme's 1px pale-blue per-class borders) after `base_css` when
    `ui/high_contrast` is on — appended, not substituted, since Qt
    stylesheets resolve same-specificity ties in favour of whichever rule
    was parsed last.
  * `apply_theme(base_css, app=None)` sets the composed stylesheet on the
    running `QApplication`.
* `app.py`'s `_load_stylesheet` now delegates to
  `accessibility.base_stylesheet` (one implementation of the repo_root path
  resolution instead of two) and `run_app` calls `apply_theme(...)` at
  startup instead of `app.setStyleSheet(stylesheet)` directly.
* `MainWindow._on_preferences_changed` calls `apply_theme(base_stylesheet(self._repo_root))`
  before its existing "some settings require a restart" message box, so
  toggling High Contrast is visible immediately without one — the other
  settings genuinely do need a restart today, so that message box stays for
  those, this just makes the one setting that doesn't need it actually not
  need it.
* `PreferencesDialog`'s User Interface tab gained two checkboxes ("High
  contrast mode", "Reduce motion"), following the exact same
  checkbox/tooltip/`_load_settings`/`_save_and_accept`/`_restore_defaults`
  pattern every other boolean field in that dialog already uses (e.g.
  `_show_tooltips_check`). Both default unchecked.
* `ui/splash_screen.py`'s two real `QPropertyAnimation` fade-outs
  (`SplashScreen.finish`, `LoadingOverlay.dismiss` — the only
  `QPropertyAnimation`/`QVariantAnimation` transitions anywhere in the app,
  confirmed by grep) now call `setDuration(reduced_motion_duration_ms(350))`
  / `(200)` instead of a bare literal. The continuously-looping spinner
  (`QTimeLine`-driven) was deliberately left alone — it's the loading
  indicator itself, not a transition, and stopping it would remove the only
  sign a long operation is still running.

**Why not repo_root-relative for the override file too:** the base theme
is only ever loaded relative to `repo_root` (an existing quirk of
`app._load_stylesheet`, assuming a `<repo_root>/src/valis_workstation/...`
source-tree layout), but `main_window.py` needs to re-load it on every
Preferences change and can't import from `app.py` to do so (`app.py`
imports `main_window` at module scope, so the reverse import would be
circular). The override QSS is instead resolved package-relatively
(`Path(__file__).resolve().parent.parent / "styles"`), which needs no
`repo_root` at all and works whether run from a checkout or an installed
wheel.

**Validation.**
* New `tests/test_accessibility_settings.py` (30 tests) — the settings
  readers' defaults/on/off behaviour; `reduced_motion_duration_ms`'s
  positive-duration guarantee; `compose_stylesheet` appending real overrides
  when on, leaving `base_css` untouched when off, and falling back
  gracefully if the overrides file is missing; `apply_theme` setting the
  composed stylesheet on a real `QApplication` and no-oping without one;
  the two Preferences checkboxes existing, defaulting unchecked, loading a
  previously-saved on/off state, and the full round trip (toggle -> save ->
  fresh dialog instance shows the persisted state); `MainWindow._on_preferences_changed`
  calling `apply_theme(base_stylesheet(repo_root))`; `app._load_stylesheet`
  still matching `accessibility.base_stylesheet` byte-for-byte; both splash
  screen fades using the normal duration when off and the near-zero one
  when on. **27 of 30 fail on the pre-fix tree** (confirmed via
  `git stash` of the four modified source files plus temporarily moving the
  three new files aside, then restoring both).
* Full suite: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -q` ->
  **394 passed** (was 364), 0 regressions.
* Targeted Preferences/app/splash batch (`test_accessibility_settings.py` +
  `test_app.py` + `test_splash_screen.py` + `test_preferences_wiring_followups.py`
  + `test_all_features.py` + `test_performance_monitoring_wiring.py`):
  **219 passed**.
* `ruff check` on the four modified files: identical finding counts
  before/after (app.py 0/0, main_window.py 12/12, preferences_dialog.py
  1/1, splash_screen.py 4/4 — all pre-existing, unrelated to this change,
  confirmed via the same stash comparison). The two new source/test files
  are clean (0 findings after fixing two straightforward `UP037`/`I001`
  hits found during development).
* This sandbox was missing `pandas`/`matplotlib` (needed transitively by
  `main_window.py` via `analysis_plot.py`/`error_metrics.py`) — installed
  alongside the already-present PySide6/pytest-qt/numpy/psutil, same
  lightweight-venv approach prior entries in this log describe; the full
  VALIS scientific stack (torch/pyvips/kornia/napari/...) was not needed.

**PR.** [#11](https://github.com/leonardolv/VALIS-GUI/pull/11).

### 2026-09-09 UTC — `MergeSlidesDialog`'s "Normalize intensities" checkbox does nothing
Branch `claude/fervent-johnson-qcsak4` · PR
[#10](https://github.com/leonardolv/VALIS-GUI/pull/10) · Status: **done**

**Claimed** from the Backlog (the only two open items were this one and
`ui/high_contrast`/`ui/reduced_motion`, which has no UI entry point at all
yet — this one is user-reachable today, so higher priority per the skill's
triage hierarchy).

**Root cause.** `MergeSlidesDialog.get_merge_config()`
(`ui/dialogs/merge_slides_dialog.py`) has always included
`"normalize": self._normalize.isChecked()` (checked by default) in the dict
it returns, but `services/merge_slides.py::merge_registered_slides` never
read that key anywhere — it built `merge_kwargs` and called
`registrar.warp_and_merge_slides(**merge_kwargs)` unconditionally.
`Valis.warp_and_merge_slides` (`valis/registration.py`) has no `normalize`
parameter of its own either, confirmed by reading its real signature. Net
effect: every multi-channel merge saved each channel's raw, unstretched
intensity range regardless of the checkbox — a `git log -S"normalize"` on
`merge_slides.py` shows the key was never referenced there in the file's
history.

**Fix.** `merge_registered_slides` now branches on
`merge_config.get("normalize")`:
- **Off** — unchanged: `registrar.warp_and_merge_slides(**merge_kwargs)`
  with `dst_f` set, VALIS builds/warps/saves in one call, exactly as before.
- **On** — `warp_and_merge_slides` is called with `dst_f=None` so it
  returns the built-but-unsaved `pyvips.Image` (plus channel names and
  OME-XML) instead of writing it. New `_normalize_channels()` linearly
  stretches each band independently (its own min -> 0, its own max -> the
  pixel format's ceiling: 255 for `uchar`, 65535 for `ushort`; an
  unsupported format or an already-flat band is left untouched rather than
  guessed at or divided by zero). The stretched image is saved directly via
  `valis.slide_io.save_ome_tiff` — lazily imported via
  `importlib.import_module`, matching the existing
  `services/valis_pipeline.py` pattern for a stack that isn't always
  installed — reusing the same tile size/compression/quality/pyramid
  options the non-normalize path would have used (falling back to
  `slide_io.get_tile_wh` off the registrar's reference slide when no
  explicit tile size was configured).

**Why this shape, not "remove the checkbox":** the checkbox's own tooltip
("Normalize intensity ranges across channels. Recommended for better
visualization.") describes exactly a per-channel min/max contrast stretch,
which is real, well-defined, standard behavior for multiplexed-imaging
tools (CyCIF/CODEX) — implementing it was the smaller-risk option that
still delivers the feature the dialog already promises, versus silently
downgrading a shipped, checked-by-default control.

**Validation.**
* New `tests/test_merge_slides_service.py` (9 tests) — unit tests for
  `_normalize_channels` against a lightweight fake mimicking the subset of
  the `pyvips.Image` API this module uses (band indexing, `min`/`max`,
  arithmetic, `cast`, `bandjoin`; real `pyvips`/VALIS aren't installed in
  this sandbox), plus integration tests for `merge_registered_slides`
  covering both branches, explicit-vs-computed tile size, mid-merge
  cancellation after the image is built but before it's saved, and
  progress-callback completion — mocking `registrar.warp_and_merge_slides`
  and `sys.modules["valis.slide_io"]`.
* All 9 tests **fail to collect (`ImportError`) on the pre-fix tree**
  (verified via `git stash` of just `services/merge_slides.py`, then
  restored).
* Full suite: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -q` ->
  **364 passed** (was 355), 0 failures/errors — this run's sandbox already
  had PySide6 installed; pandas/matplotlib/numpy/psutil/pytest-qt were
  additionally installed (lightweight, same as prior runs' venvs) — the
  full `uv sync` VALIS scientific stack (torch/pyvips/kornia/...) was not
  needed and not installed, by design (the touched code lazily imports
  `valis.slide_io` only on the normalize path, and tests mock it out).
* `ruff check src/valis_workstation/services/merge_slides.py
  tests/test_merge_slides_service.py`: all checks passed, 0 findings.
* `WORKSTATION_CHANGELOG.md` gains a matching 2026-09-09 entry.

**PR.** [#10](https://github.com/leonardolv/VALIS-GUI/pull/10).

### 2026-09-08 UTC — Save Options' Format/Write-pyramid choices were silently discarded
Branch `claude/fervent-johnson-im7ui8` · PR
[#9](https://github.com/leonardolv/VALIS-GUI/pull/9) · Status: **done**

**Claimed:** the Backlog was empty of actionable items (both prior entries
were already resolved and decided), so this run did a fresh code audit
instead of reading the log, per the task's own fallback instruction.

**Root cause.** `Config` (`models/config.py`) documents "every field here has
a matching widget in `PropertiesDock`" — true for every field except
`image_format` and `write_pyramid`, which `PropertiesDock.config()`
(`ui/properties_dock.py:587-588`, pre-fix) hardcoded to `"OME-TIFF"`/`True`
because no widget for either existed anywhere in the dock. Meanwhile
`SaveOptionsDialog` (`ui/dialogs/save_options_dialog.py`) has real Format and
"Write image pyramid" controls, and `MainWindow._show_save_options`
(`main_window.py`) read both out of `dialog.get_options()` and then dropped
them on the floor — it copied `pyramid_levels`/`compression`/`tile_size`/
`quality` into the dock's spinboxes but had nowhere to put the other two.
Net effect: no matter what a user picked in the Save Options dialog, every
registration run always saved OME-TIFF with pyramids on
(`services/valis_pipeline.py:395,469` read `config.write_pyramid`/
`config.image_format` straight from the always-hardcoded `Config`). The
status bar's "Output settings updated" message was true for 4 of the 6
options shown in the dialog that had just closed.

**Fix.** Added `_format_combo` (a `QComboBox` over `ImageFormats.all()`) and
`_write_pyramid_check` (a `QCheckBox`, wired to enable/disable
`_pyramid_levels_spin` exactly like `SaveOptionsDialog`'s own copy already
does) to `PropertiesDock`'s Output Settings group. `config()`/`set_config()`
now read/write both instead of hardcoding, and `_show_save_options` applies
`options["format"]`/`options["write_pyramid"]` to the new widgets alongside
the four it already copied.

**Validation.** 4 new tests (`tests/test_all_features.py`:
`TestMainWindow.test_show_save_options_applies_format_and_write_pyramid`,
`TestPropertiesDockSync.test_all_image_formats_in_combobox`/
`test_image_format_and_write_pyramid_round_trip`/
`test_write_pyramid_toggle_enables_pyramid_levels`) — **all 4 fail
`AttributeError` on the pre-fix tree** (verified by `git stash`-ing just the
two source files and re-running). Full suite: **355 passed** (was 351), 0
regressions — run with `QT_QPA_PLATFORM=offscreen pytest tests/ -q` against a
lightweight venv (PySide6/pytest-qt/psutil/matplotlib/pandas/numpy; the
repo's full `uv sync` lockfile pulls in the entire VALIS scientific stack
including several GB of CUDA wheels, which this sandbox's network/disk
couldn't accommodate in reasonable time — the GUI test files under test
don't need any of it, confirmed by the run being green). `ruff check` on
both touched source files: 16 findings before and after (0 new; all
pre-existing blind-exception/style findings elsewhere in `properties_dock.py`
this change didn't touch).

**PR.** [#9](https://github.com/leonardolv/VALIS-GUI/pull/9).

### 2026-08-19 (3) — `validate_slides`'s disk-space check no longer falls back to cwd

**Item claimed and finished in one pass.** Not a Backlog carry-over — the
Backlog was fully exhausted of open items at the start of this run (both
remaining entries are struck-through "Done" records referencing prior
Completed entries), so this run scanned the codebase directly instead.

**Root cause.** `validate_slides` (`src/valis_workstation/utils/validation.py`)
computed its free-disk-space check target as:

```python
disk_usage = shutil.disk_usage(
    output_dir.parent if output_dir.exists() else Path.cwd()
)
```

`output_dir` is built fresh on every registration run
(`self._repo_root / "output" / config.project_name`, `main_window.py`) and is
only actually created later in the *same function* (the "is output directory
writable" check, further down, calls `output_dir.mkdir(parents=True,
exist_ok=True)`). So on the ordinary first-run case for any new project
name, `output_dir.exists()` is `False` at the point the space check runs, and
it silently checked the process's current working directory instead —
which has no necessary relation to where the multi-gigabyte registration
output will actually land. `repo_root` (hence `output_dir`) derives from
`Path(__file__).resolve()`, not from the process cwd, so the two can be on
different filesystems (different launcher, different mount, symlinked/
network output drive) — in exactly that case, the "insufficient/low disk
space" errors and warnings become meaningless.

**Solution.** Replaced the `exists()`-gated single-level fallback with a walk
up `output_dir.resolve()` to its nearest existing ancestor:

```python
disk_check_path = output_dir.resolve()
while not disk_check_path.exists():
    disk_check_path = disk_check_path.parent
disk_usage = shutil.disk_usage(disk_check_path)
```

`.resolve()` makes the path absolute first, so the walk is guaranteed to
terminate at the filesystem root (which always exists) rather than looping
forever on a relative path whose `.parent` chain can settle on `Path('.')`.
This always checks a directory that is actually on `output_dir`'s own
filesystem, whether or not `output_dir` itself has been created yet.

**Validation.** New test
`TestValidateSlides::test_disk_space_check_targets_output_dir_not_cwd`
(`tests/test_validation.py`) monkeypatches `shutil.disk_usage` to record what
path it was called with, points the process cwd somewhere unrelated via
`monkeypatch.chdir`, and asserts the checked path is under `output_dir`'s own
tree rather than equal to cwd. Confirmed **red on the pre-fix code** (reverted
the production change, reran — the check landed on the unrelated cwd) and
green after. `tests/test_validation.py` (9 tests) and
`tests/test_all_features.py::TestValidation` (2 tests) pass. `ruff check` on
both changed files: same 2 pre-existing findings before and after (0 new).
Full app-wide suite not run in this pass — this repo's dependency set
(napari, JPype/scyjava, VALIS itself) is heavy enough that installing it was
out of scope for a fix this narrow; confirmed instead that `validate_slides`
has exactly two callers in the whole tree (`main_window.py` and the two test
files above), both exercised by the tests run.

**PR.** [#8](https://github.com/leonardolv/VALIS-GUI/pull/8).

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
~~**`MergeSlidesDialog`'s "Normalize intensities" checkbox does nothing.**~~
  Done by the 2026-09-09 run — see the Completed entry. Implemented
  per-channel min/max intensity normalization on the merged image before it
  is saved, rather than removing the checkbox.
  (original entry follows)
- **`MergeSlidesDialog`'s "Normalize intensities" checkbox does nothing.**
  Found by the 2026-09-08 audit that also found the Save Options item above
  (backup candidate #1). `ui/dialogs/merge_slides_dialog.py`'s `_normalize`
  checkbox is included in `get_merge_config()`'s returned dict
  (`"normalize": self._normalize.isChecked()`), but a repo-wide grep for
  `normalize` in `services/merge_slides.py` finds it only in a docstring —
  `merge_registered_slides` never reads `merge_config["normalize"]`. Smaller
  blast radius than the Save Options bug (only the optional multi-channel
  merge feature is affected). Needs a decision before it's a small fix:
  implement per-channel intensity normalization before
  `registrar.warp_and_merge_slides`, or remove the checkbox as
  not-yet-implemented.
~~**`ui/high_contrast`/`ui/reduced_motion` settings keys are fully dead.**~~
  Done by the 2026-09-15 run — see the Completed entry. Wired both into
  Preferences (two new checkboxes) plus real behaviour (a genuine
  high-contrast QSS variant, and shortened/skipped `QPropertyAnimation`
  fades) rather than deleting them.
  (original entry follows)
- **`ui/high_contrast`/`ui/reduced_motion` settings keys are fully dead.**
  Also found by the 2026-09-08 audit (backup candidate #2). `settings_keys.py`
  defines both, but a repo-wide grep finds zero readers/writers and no
  corresponding checkbox anywhere, including `PreferencesDialog` — unlike the
  Preferences items resolved by earlier runs in this log (2026-08-18/19),
  these two have no UI entry point at all yet, so no user can reach them
  today. Lower priority than the two items above: scaffolding for an
  accessibility feature that was never wired up, not a defect a user can
  stumble into.
