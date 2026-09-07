# GUI & UX Maintenance Log

## In Progress

## Blocked / Needs Review

## Completed

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
