# VALIS Workstation Release Notes

## 2026-03-22

This release focuses on workflow quality-of-life improvements, stronger reliability in Qt UI behavior, and better run diagnostics/export support.

### Highlights

- Added a first-run setup wizard for default project/output profile initialization.
- Added configuration presets (save/load/delete) and output profile templates.
- Added a preflight estimate step before registration start.
- Added resume support for the last run context.
- Added session bundle export (ZIP) for support/handoff.
- Added a diagnostics dialog with runtime/environment context.
- Improved loading overlays with stage/progress/ETA feedback.
- Added slide preview filtering and sorting controls.
- Added layer controls enhancements: search, lock edits, solo selected, reset opacity.
- Added blink viewer comparison modes: `Blink`, `Side-by-side`, `Swipe`.

### Added

- First-run wizard:
  - `src/valis_workstation/ui/dialogs/first_run_wizard.py`
  - integrated in `src/valis_workstation/app.py`
- Diagnostics dialog:
  - `src/valis_workstation/ui/dialogs/diagnostics_dialog.py`
  - integrated in `src/valis_workstation/main_window.py`
- Form-layout spacer helper:
  - `src/valis_workstation/ui/form_layout_utils.py`
- Session bundle export action (`Tools -> Export Session Bundle...`) in:
  - `src/valis_workstation/main_window.py`

### Changed

- Constants migrated to `StrEnum` for safer iteration/value behavior:
  - `src/valis_workstation/constants.py`
- Recent folder handling now includes missing-folder indicators and linked-config reopen support:
  - `src/valis_workstation/main_window.py`
- Status dock now shows a stage label and safer cancel rebinding:
  - `src/valis_workstation/ui/status_dock.py`
- Documentation refreshed for current behavior and menus:
  - `VALIS-GUI-Manual.html`
  - `VALIS-GUI-Tutorial.html`
  - `README_VALIS_WORKSTATION.md`

### Fixed

- Resolved invalid `QFormLayout.addStretch()` usage in dialogs:
  - `src/valis_workstation/ui/dialogs/performance_stats_dialog.py`
  - `src/valis_workstation/ui/dialogs/preferences_dialog.py`
- Hardened layer controls for non-evented/list-based layer providers:
  - `src/valis_workstation/ui/layer_controls_dock.py`
- Prevented first-run setup from being marked completed if wizard is canceled:
  - `src/valis_workstation/app.py`
- Removed duplicate config-load path when opening recent folder+config entries:
  - `src/valis_workstation/main_window.py`

### Testing

- Added/updated regression coverage in `tests/test_all_features.py` for:
  - form-layout dialog construction
  - output profile templates
  - main-window startup performance smoke guard
  - modal dialog stubs and thumbnail monkeypatch signature compatibility
- Targeted post-fix validation:
  - `tests/test_all_features.py::TestMainWindow::test_open_slide_folder`
  - `tests/test_all_features.py::TestMainWindow::test_drop_folder`
  - `tests/test_all_features.py::TestMainWindow::test_open_folder_cancelled`
  - Result: `3 passed`

### Notes

- Blink viewer `Side-by-side` and `Swipe` are practical UI-level comparison modes built on current layer stack behavior.
- For full implementation details, see `WORKSTATION_CHANGELOG.md`.

## 2026-04-11 Addendum

### Documentation Corrections

- Updated manual references to HTML docs in the repository root:
  - `VALIS-GUI-Manual.html`
  - `VALIS-GUI-Tutorial.html`
- Roadmap/docs corrected to reflect that registration cancellation is implemented.

### Upstream VALIS Check

- Upstream repository checked at `MathOnco/valis` `v1.2.0`.
- Local bundled `valis/` matches upstream version at audit time; no core-library sync delta found.
