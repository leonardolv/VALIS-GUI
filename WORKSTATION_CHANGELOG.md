# VALIS Workstation Changelog

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
