# GUI & UX Maintenance Log

## In Progress

## Blocked / Needs Review

## Completed

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
- Add thumbnail caching for large whole-slide image formats.
- Implement batch export options for registered slide sets.
