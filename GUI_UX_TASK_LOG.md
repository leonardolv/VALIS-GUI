# GUI & UX Maintenance Log

## In Progress

## Blocked / Needs Review

## Completed

### Task: Add Error Detail Dialog Accessibility, Pointing Hand Cursors, Lifetime-Safe Clipboard Copy, and Headless Safety
- **Completed**: 2026-10-02
- **Changes**:
  - `src/valis_workstation/ui/dialogs/error_detail_dialog.py`:
    - Exposed buttons as instance attributes (`copy_btn`, `report_btn`, `close_btn`) and collapsible group as `details_group` and text edit as `details_text`.
    - Added screen-reader accessible names, descriptive tooltips, and `PointingHandCursor` shapes across all dialog buttons and the collapsible technical details group.
    - Added lifetime-safe timer callback handling (`singleShot(2000, self, ...)` with `RuntimeError` guards) to prevent object deletion exceptions when dialog is closed during copy confirmation.
    - Added headless/pytest offscreen execution guards to `_report_issue` and `show_error_dialog` to prevent blocking modal popups during automated test runs.
  - `tests/test_error_detail_dialog.py`:
    - Added comprehensive unit tests validating accessible names, tooltips, cursor shapes, copy to clipboard action, and headless safety across `ErrorDetailDialog` and `show_error_dialog`.
- **Verification**: Verified headlessly with `pytest tests/test_error_detail_dialog.py tests/test_performance_stats_dialog.py tests/test_diagnostics_dialog.py -q` (10 passed, 0 failures in 0.47s) and `pytest tests/test_all_features.py -k ErrorDetailDialog -v` (4 passed in 0.39s).
- **Status**: Completed

### Task: Add Performance Statistics Dialog Accessibility and Headless Cache Safety
- **Completed**: 2026-10-02
- **Changes**:
  - `src/valis_workstation/ui/dialogs/performance_stats_dialog.py`:
    - Added screen-reader accessible names, descriptive tooltips, and pointing hand cursors for `_refresh_btn`, `_clear_thumb_cache_btn`, and `_close_btn`.
    - Added accessible name `"Thumbnail Cache Usage"` for the cache progress bar `_thumb_cache_bar`.
    - Added headless/test environment safety guard to `_clear_thumbnail_cache` to prevent modal popup blocking during automated test runs.
  - `tests/test_performance_stats_dialog.py`:
    - Added comprehensive unit tests validating accessible names, tooltips, cursor shapes, refresh trigger, and headless cache clearing.
- **Verification**: Verified headlessly with `pytest tests/test_performance_stats_dialog.py tests/test_all_features.py -q` (126 passed, 0 failures).
- **Status**: Completed

### Task: Add Diagnostics Dialog Clipboard Copy, Safe Lifetime Handling, and Accessibility Affordances
- **Completed**: 2026-10-02
- **Changes**:
  - `src/valis_workstation/ui/dialogs/diagnostics_dialog.py`:
    - Added "Copy to Clipboard" button (`self._copy_btn`) with inline visual `✓ Copied!` confirmation.
    - Attached context object `self` and `RuntimeError` exception protection to timer callback to prevent Qt object lifecycle errors when dialog is closed before timeout.
    - Added accessible names, descriptive tooltips, and `PointingHandCursor` across all controls (`_text`, `_refresh_btn`, `_copy_btn`, `_close_btn`).
  - `tests/test_diagnostics_dialog.py`:
    - Added unit tests validating accessibility metadata, tooltips, clipboard copy, and refresh functionality.
- **Verification**: Verified headlessly with `pytest tests/test_diagnostics_dialog.py -v` (3 passed in 0.51s) and `pytest tests/test_layout_splitters.py -v` (53 passed).
- **Status**: Completed

### Task: Remediate Pipeline Dictionary Log Formatting and Test Logger Propagation
- **Completed**: 2026-10-02
- **Changes**:
  - `src/valis_workstation/services/valis_pipeline.py`:
    - Converted `kwargs` and `vars(config)` dictionary arguments in `logger.info` calls to `str(...)` to avoid Python logging `TypeError: not all arguments converted during string formatting` when logging dictionaries with `%s`.
  - `tests/conftest.py`:
    - Added `_restore_valis_logging_propagation` fixture ensuring `valis_workstation` logger propagates to root during testing so `caplog` captures service logs reliably across the entire test suite.
- **Verification**: Verified headlessly with `pytest tests/ -q` (439 passed, 0 failures in 24.79s).
- **Status**: Completed
- **Changes**:
  - `src/valis_workstation/ui/dialogs/save_options_dialog.py`:
    - Added batch export presets (`Default (Balanced OME-TIFF)`, `Diagnostic High-Quality`, `Web / Fast Preview`, `Archival Lossless`, `Custom`) via `self._preset_combo`, allowing fast scenario-based configuration of formats, pyramid levels, compression, quality, and tile sizes.
    - Added `initial_options: dict | None = None` support to `SaveOptionsDialog.__init__` and `apply_options()` to seamlessly pre-populate the dialog from active Properties dock output settings.
    - Added "Reset to Defaults" button (`QtWidgets.QDialogButtonBox.StandardButton.Reset`) restoring recommended workstation defaults in a single click.
    - Added full screen reader accessible names and descriptive tooltips across all dialog controls (`_preset_combo`, `_write_pyramid`, `_pyramid_levels`, `_compression`, `_quality`, `_tile_size`, `_format`, `_info_label`, `reset_defaults_btn`).
  - `src/valis_workstation/main_window.py`:
    - Updated `_show_save_options()` to pass current output parameters from `_properties_dock` into `SaveOptionsDialog(self, initial_options=current_options)`.
  - `tests/test_save_options_dialog.py`:
    - Added comprehensive unit tests validating initial options mapping, preset switching, custom modifications, accessibility names, and reset to defaults.
- **Verification**: Verified headlessly with `pytest tests/test_save_options_dialog.py tests/test_all_features.py -k "SaveOptions" -v` (9 passed, 0 failures).
- **Status**: Completed

### Task: Enhance ROI Export Dialog with JSON Import/Export, Reset to Defaults, and Non-blocking Feedback
- **Completed**: 2026-09-25
- **Changes**:
  - `src/valis_workstation/ui/dialogs/roi_export_dialog.py`:
    - Replaced blocking `QMessageBox.information` modal on clipboard copy with inline visual status banner (`_feedback_label`), eliminating workflow disruption.
    - Added "Paste from JSON" action (`self.paste_json_btn`) to parse and populate `x`, `y`, `width`, `height`, and `format` directly from clipboard JSON with real-time feedback.
    - Added "Reset to Defaults" button (`QtWidgets.QDialogButtonBox.StandardButton.Reset`) restoring coordinates and export settings to standard defaults.
    - Added accessible names and tooltips across all form inputs and action buttons (`X Coordinate Pixels`, `Y Coordinate Pixels`, `Width Pixels`, `Height Pixels`, `Export Image Format`, `Reopen in Viewer`, `Copy Coordinates as JSON`, `Paste Coordinates from JSON`, `Reset to Defaults`).
  - `tests/test_roi_export_dialog.py`:
    - Created comprehensive unit tests validating defaults, accessible names, copy to JSON, paste from JSON, invalid JSON handling, and reset to defaults.
- **Verification**: Verified headlessly with `pytest tests/test_roi_export_dialog.py -v` (5 passed in 0.58s).
- **Status**: Completed

### Task: Fix scikit-image ImportError crash in _get_transformer_cls fallback
- **Completed**: 2026-09-07
- **Changes**:
  - `src/valis_workstation/services/valis_pipeline.py`:
    - Resolved circular `ModuleNotFoundError: No module named 'skimage'` where `_get_transformer_cls` caught `ImportError` from `skimage` and then erroneously attempted `from skimage.transform import SimilarityTransform`.
    - Introduced a safe, standalone `SimilarityTransform` placeholder class fallback with logging when `scikit-image` is not installed or importable.
  - `tests/test_pipeline.py`:
    - Added `test_transformer_cls_scikit_image_import_error_fallback` verifying that `_get_transformer_cls` cleanly falls back to `SimilarityTransform` without raising when `skimage` imports fail.
- **Verification**: Verified with `pytest tests/ -v` (327 passed, 0 failures across the complete test suite in 32.26s).
- **Status**: Completed


### Task: Restore MainWindow constructor backward compatibility, worker signal fallback, and resilient dock signals
- **Completed**: 2026-09-07
- **Changes**:
  - `src/valis_workstation/main_window.py`:
    - Added default argument `gpu_available: bool = False` to `MainWindow.__init__` to ensure backwards compatibility with 3-arg call sites (`app.py`, test fixtures).
    - Guarded `_project_dock.count_changed` and `_slide_preview_dock.count_changed` signal connections using `hasattr`.
    - Hardened `_update_left_tab_titles` against missing dock attributes or uninitialized tabs.
  - `src/valis_workstation/workers/valis_worker.py`:
    - Added `@property def _cancel_requested` getter/setter wrapping `_cancel_event` to restore compatibility with cancellation assertion tests.
    - Added dynamic fallback for `run_valis_pipeline` when pipeline functions or test mocks do not accept `stage_callback`.
  - `src/valis_workstation/ui/status_dock.py`:
    - Added `_show_status_message` helper to safely check `hasattr(win, "statusBar")` and prevent `AttributeError` when `StatusDock` is unparented or parented to a non-`QMainWindow`.
  - `src/valis_workstation/ui/project_dock.py` & `src/valis_workstation/ui/slide_preview_dock.py`:
    - Added `count_changed = QtCore.Signal(int)` to both docks, emitted when slides or previews are added, removed, or filtered.
    - Added `SlidePreviewDock.slide_count()` method returning total thumbnail count.
  - `tests/test_models.py` & `tests/test_all_features.py`:
    - Updated `Config` field count assertions and expected dictionary key sets to match the 23 fields added in VALIS v1.2.0.
  - `tests/test_gui_components.py`:
    - Mocked `QMessageBox.question` in `TestStatusDock.dock` fixture to adhere to headless test standards and ensure clean non-interactive log clearing.
- **Verification**: Verified with `pytest tests/ -q` (326 passed, 0 failures across the complete test suite).
- **Status**: Completed

## Backlog
- ~~Add thumbnail caching for large whole-slide image formats.~~ (Completed in `ThumbnailCache` and `thumbnail_generator.py`)
- ~~Implement batch export options for registered slide sets.~~ (Completed via `SaveOptionsDialog` batch export presets)
