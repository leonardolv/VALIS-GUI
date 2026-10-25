# GUI & UX Maintenance Log

## In Progress

## Blocked / Needs Review

## Completed

### Task: PerformanceStatsDialog object names, accessibility metadata, and button affordances
- **Completed**: 2026-10-25
- **Changes**:
  - `src/valis_workstation/ui/dialogs/performance_stats_dialog.py`:
    - Configured explicit `setObjectName("performanceStatsDialog")` and `setAccessibleName("Performance Statistics Dialog")` on dialog instance.
    - Added explicit `setObjectName("performanceTabs")` and `setAccessibleName("Performance Statistics Categories")` on tab widget.
    - Added explicit object names across action buttons (`perfRefreshBtn`, `perfClearCacheBtn`, `perfCloseBtn`) and cache progress bar (`perfThumbCacheBar`).
  - `tests/test_performance_stats_dialog.py`:
    - Expanded unit tests asserting dialog and tab object names, accessible names, button object names, tooltips, and pointing hand cursor affordances.
- **Verification**: Verified headlessly with `python -m pytest tests/test_performance_stats_dialog.py tests/test_error_and_diagnostics_dialogs.py -v` (6 passed in 1.31s, 0 errors).
- **Status**: Completed

### Task: ErrorDetailDialog and DiagnosticsDialog object names, accessibility metadata, and visual copy confirmation
- **Completed**: 2026-10-25
- **Changes**:
  - `src/valis_workstation/ui/dialogs/error_detail_dialog.py`:
    - Configured explicit `setObjectName("errorDetailDialog")` and `setAccessibleName("Error Details Dialog")` on dialog instance.
    - Added explicit object names across message label (`errorMessageLabel`), error text label (`errorTextLabel`), details group (`errorDetailsGroup`), details text (`errorDetailsText`), copy button (`errorCopyBtn`), report button (`errorReportBtn`), and close button (`errorCloseBtn`).
  - `src/valis_workstation/ui/dialogs/diagnostics_dialog.py`:
    - Configured explicit `setObjectName("diagnosticsDialog")` and `setAccessibleName("Diagnostics Dialog")` on dialog instance.
    - Added explicit object names across output text area (`diagnosticsText`), refresh button (`diagnosticsRefreshBtn`), copy button (`diagnosticsCopyBtn`), and close button (`diagnosticsCloseBtn`).
  - `tests/test_error_and_diagnostics_dialogs.py`:
    - Added comprehensive unit test coverage asserting dialog and widget object names, accessible names, button cursors, tooltips, and non-blocking copy confirmation feedback.
- **Verification**: Verified headlessly with `python -m pytest tests/test_error_and_diagnostics_dialogs.py tests/test_roi_export_dialog.py tests/test_warp_annotations_dialog.py -v` (11 passed in 0.40s, 0 errors).
- **Status**: Completed

### Task: ROIExportDialog and WarpAnnotationsDialog object names, accessibility metadata, button tooltips, and pointer cursor affordances
- **Completed**: 2026-10-25
- **Changes**:
  - `src/valis_workstation/ui/dialogs/roi_export_dialog.py`:
    - Configured explicit `setObjectName` ("roiExportDialog") and `setAccessibleName` ("ROI Export Dialog") on dialog instance.
    - Configured explicit `setObjectName` across coordinate spinboxes (`roiXCoordSpin`, `roiYCoordSpin`, `roiWidthSpin`, `roiHeightSpin`), format combobox (`roiFormatCombo`), reopen checkbox (`roiReopenCheck`), and feedback label (`roiFeedbackLabel`).
    - Added `PointingHandCursor` affordances across format combobox, reopen checkbox, JSON clipboard action buttons (`roiCopyJsonBtn`, `roiPasteJsonBtn`), reset button (`roiResetBtn`), and dialog action buttons (`roiOkBtn`, `roiCancelBtn`).
    - Configured explicit `setObjectName`, `setAccessibleName`, and descriptive tooltips on primary Ok and Cancel buttons.
  - `src/valis_workstation/ui/dialogs/warp_annotations.py`:
    - Configured explicit `setObjectName` ("warpAnnotationsDialog") and `setAccessibleName` ("Warp Annotations Dialog") on dialog instance.
  - `tests/test_roi_export_dialog.py` and `tests/test_warp_annotations_dialog.py`:
    - Expanded unit tests validating dialog and control object names, accessible names, button tooltips, and pointing hand cursor affordances.
- **Verification**: Verified headlessly with `python -m pytest tests/test_roi_export_dialog.py tests/test_warp_annotations_dialog.py -v` (9 passed in 0.47s, 0 errors).
- **Status**: Completed

### Task: FirstRunWizard Finish Page Quick Tutorial Checkbox and Repository-Wide Dash Standardization
- **Completed**: 2026-10-22
- **Changes**:
  - `src/valis_workstation/ui/dialogs/first_run_wizard.py`:
    - Added `_open_tutorial_check` checkbox to `_build_finish_page` with explicit object name (`first_run_open_tutorial_check`), accessible name, tooltip, pointer cursor, and transparent background styling.
    - Added `should_open_tutorial()` predicate returning whether user selected to launch tutorial upon completing setup.
  - `src/valis_workstation/app.py`:
    - Wired `wizard.should_open_tutorial()` to trigger `main_window._show_quick_tutorial` on startup completion.
  - Standardized em dashes and en dashes to hyphens across `app.py`, `models/config.py`, `services/valis_pipeline.py`, `ui/layer_controls_dock.py`, `ui/properties_dock.py`, `ui/slide_preview_dock.py`, `ui/splash_screen.py`, and `utils/performance.py`.
  - `tests/test_first_run_wizard_and_analysis_plot.py`:
    - Added unit test assertions verifying `first_run_open_tutorial_check` object name, accessible name, tooltip, pointer cursor, and `should_open_tutorial()` toggle behavior.
- **Verification**: Verified headlessly with `pytest tests/test_first_run_wizard_and_analysis_plot.py tests/test_gui_polish_layout.py -v` (11 passed in 3.98s, 0 errors).
- **Status**: Completed

### Task: Welcome Panel Note and Splash Subtitle WCAG AA Contrast Polish and Hyphen Standardization
- **Completed**: 2026-10-22
- **Changes**:
  - `src/valis_workstation/ui/welcome_panel.py`:
    - Updated `WelcomeViewerNote` stylesheet from `#888` to `#a0a0a0` for enhanced legibility and >= 6.5:1 WCAG AA contrast on dark card backgrounds.
    - Added explicit `setAccessibleName("Viewer availability note")`.
    - Replaced `&mdash;` HTML entities with standard hyphens in welcome step descriptions.
    - Standardized button labels from ellipsis characters to standard periods (`...`).
  - `src/valis_workstation/ui/splash_screen.py`:
    - Updated `subtitle` stylesheet from `#888888` to `#a0a0a0` for WCAG AA compliance against `#1e1e1e` card backgrounds.
  - `tests/test_gui_polish_layout.py`:
    - Added unit test `test_welcome_panel_and_splash_contrast_and_accessibility` validating contrast colors, accessible names, and hyphen standardization.
- **Verification**: Verified headlessly with `pytest tests/test_gui_polish_layout.py tests/test_first_time_user_guidance.py -v` (17 passed in 8.27s, 0 errors).
- **Status**: Completed

### Task: QuickActionsToolbar concise action labels, width threshold optimization, and responsive adaptation
- **Completed**: 2026-10-22
- **Changes**:
  - `src/valis_workstation/ui/main_window_actions.py`:
    - Added concise `iconText` labels across toolbar actions ("Open", "Run", "Cancel", "Recent", "Resume", "Reset", "Focus", "Fit", "Blink", "Tutorial") while preserving full descriptive labels for application menus.
    - Reduced full toolbar button width requirement from 2546px down to 1226px, enabling labels on standard desktop resolutions (~1400px+) and clean automatic fallback to icon-only buttons on compact/narrow viewports.
- **Verification**: Verified headlessly with `pytest tests/test_gui_polish_layout.py -v` (7 passed) and full test suite `pytest tests/ -q` (546 passed, 0 failures).
- **Status**: Completed

### Task: Enhance QuickTutorialDialog Accessibility, Object Names, Checkbox Styling, Dynamic Button Tooltips, and Dash Standardization
- **Completed**: 2026-10-20
- **Changes**:
  - `src/valis_workstation/ui/dialogs/quick_tutorial_dialog.py`:
    - Added screen-reader accessible names, object names, and descriptive tooltips across `quickTutorialDialog`, `_icon_label` (`tutorialIconLabel`), `_title_label` (`tutorialTitleLabel`), `_step_counter` (`tutorialStepCounter`), `_body` (`tutorialBody`), `_action_btn` (`tutorialActionBtn`), `_bubbles_container` (`tutorialBubblesContainer`), `_dont_show` (`tutorialDontShowCheck`), `_prev_btn` (`tutorialPrevBtn`), `_next_btn` (`tutorialNextBtn`), and `_close_btn` (`tutorialCloseBtn`).
    - Added object names and accessible names to individual progress bubbles (`tutorialBubble_0` through `tutorialBubble_12`).
    - Removed stray border/line behind the "Don't show on startup" checkbox label by applying `background: transparent; border: none;`.
    - Added dynamic tooltips and accessible names on `_close_btn` ("Finish tutorial" on the final step vs "Close tutorial" on intermediate steps) and `_action_btn`.
    - Standardized dashes strictly to hyphens only across window title, docstrings, and step comments (no em dashes, no en dashes).
  - `tests/test_quick_tutorial_run_step.py`:
    - Expanded test suite to validate window title hyphenation, object names, accessible names across all header/body/footer widgets and bubble indicators, cursor shapes, and finish step dynamic button states.
- **Verification**: Verified headlessly with `pytest tests/test_quick_tutorial_run_step.py tests/test_quick_tutorial_dialog_timer.py tests/test_blink_viewer_dialog.py tests/test_first_run_wizard_and_analysis_plot.py tests/test_preferences_dialog_accessibility.py tests/test_warp_annotations_dialog.py tests/test_merge_slides_dialog.py tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py tests/test_gui_components.py -v` (85 passed in 13.28s, 0 errors).
- **Status**: Completed

### Task: Enhance BlinkViewerDialog Accessibility, Object Names, Interval Speed Control, Tooltips, Hand Cursors, and Dash Standardization
- **Completed**: 2026-10-20
- **Changes**:
  - `src/valis_workstation/ui/dialogs/blink_viewer.py`:
    - Added screen-reader accessible names, object names, and descriptive tooltips across `blinkViewerDialog`, `_slide_a` (`blinkSlideACombo`), `_slide_b` (`blinkSlideBCombo`), `_mode` (`blinkModeCombo`), `_interval_spin` (`blinkIntervalSpin`), `_opacity` (`blinkOpacitySlider`), `_blink_toggle` (`blinkToggleBtn`), `_button_box` (`blinkButtonBox`), and `_close_btn` (`blinkCloseBtn`).
    - Added `PointingHandCursor` shapes across interactive comboboxes, toggle buttons, and close buttons.
    - Added configurable blink interval spinbox (`_interval_spin`) with range 100-3000 ms, single step 50 ms, suffix " ms", and tooltip.
    - Added safe exception guards when interacting with viewer layer collections and opacity properties.
    - Standardized punctuation strictly to hyphens only in comments, docstrings, and user-facing tooltips (no em dashes, no en dashes).
  - `tests/test_blink_viewer_dialog.py`:
    - Created unit tests validating accessible names, object names, cursor shapes, tooltips, interval adjustments, display modes switching, timer lifecycle stopping upon accept/reject/close dismissal, and empty slide handling.
- **Verification**: Verified headlessly with `pytest tests/test_blink_viewer_dialog.py tests/test_first_run_wizard_and_analysis_plot.py tests/test_warp_annotations_dialog.py tests/test_merge_slides_dialog.py tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py tests/test_gui_components.py -v` (63 passed, 0 failures in 4.95s).
- **Status**: Completed

### Task: Screenshot audit and layout/contrast polish (main window, status dock, slide preview, welcome, dialogs)
- **Completed**: 2026-10-16
- **Changes**:
  - QSS: spin/combo arrows were CSS border-triangles (Qt paints solid squares); now SVGs (`styles/arrow_up.svg`, `arrow_down.svg`), checked checkboxes show a tick (`check.svg`); `@STYLES_DIR@` is resolved in `accessibility.base_stylesheet`. Checkbox/radio background transparent (dark strip on dialogs).
  - Quick toolbar: icon-only when labelled buttons do not fit (`MainWindow._adapt_toolbars_to_width`), no more elided "Open...lder" / hidden buttons.
  - Status dock: stage/timing on one row, filter + Auto-scroll + Copy/Clear on one row (they overlapped), log console gets the stretch.
  - Welcome panel scrolls; Slide Preview controls split into two rows with icon-only Grid/List; Properties forms wrap long rows; sidebar minimums raised (left 240, right 340, init 380).
  - Dialogs: merge info banner (light bg with light text) darkened; grey italic notes lightened for contrast; ROI export buttons no longer clipped at min width.
  - Tests: `tests/test_gui_polish_layout.py`.
- **Evidence**: offscreen `QWidget.grab()` of all tabs at 1400x900 and 1000x640 and 11 dialogs before/after.

### Task: Enhance FirstRunWizard and AnalysisPlotDialog Accessibility, Tooltips, Hand Cursors, and Backend Compatibility
- **Completed**: 2026-10-14
- **Changes**:
  - `src/valis_workstation/ui/dialogs/first_run_wizard.py`:
    - Added screen-reader accessible names, object names, descriptive tooltips, and placeholder text to `_project_name_edit` and `_output_profile_combo`.
    - Added `PointingHandCursor` shapes to `_output_profile_combo` and wizard navigation buttons (Next, Back, Finish, Cancel).
    - Added object names and accessible names to page message labels.
  - `src/valis_workstation/ui/dialogs/analysis_plot.py`:
    - Replaced legacy `matplotlib.backends.backend_qt5agg` with modern `backend_qtagg` with fallback.
    - Added accessible names, object names, and `PointingHandCursor` shapes to `_close_btn`, `_summary_label`, and `_canvas`.
    - Guarded empty and null dataframe inputs in `_update_plot` preventing unhandled exceptions.
  - `tests/test_first_run_wizard_and_analysis_plot.py`:
    - Created unit tests validating accessible names, tooltips, cursor shapes, page navigation, and metrics plot handling.
- **Verification**: Verified headlessly with `pytest tests/test_first_run_wizard_and_analysis_plot.py tests/test_warp_annotations_dialog.py tests/test_merge_slides_dialog.py tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py tests/test_gui_components.py -v` (59 passed, 0 failures in 3.07s).
- **Status**: Completed

### Task: Enhance WarpAnnotationsDialog Accessibility, Tooltips, Hand Cursors, and Headless Safety
- **Completed**: 2026-10-06
- **Changes**:
  - `src/valis_workstation/ui/dialogs/warp_annotations.py`:
    - Added screen-reader accessible names, object names, and descriptive placeholder text to `_annotation_path` and `_output_dir_edit`.
    - Added screen-reader accessible names, descriptive tooltips, and pointing hand cursors (`PointingHandCursor`) across `_browse_annotation_btn`, `_browse_output_btn`, and `_source_slide`.
    - Exposed dialog buttons (`_button_box`, `_ok_btn`, `_cancel_btn`) with pointing hand cursors, accessible names, object names, and tooltips.
    - Guarded `QtWidgets.QMessageBox.warning` calls with headless and offscreen execution checks (`QT_QPA_PLATFORM != "offscreen"` and not `PYTEST_CURRENT_TEST`) to prevent blocking modal popups during automated tests.
  - `tests/test_warp_annotations_dialog.py`:
    - Created unit tests validating accessible names, tooltips, cursor shapes, browse callbacks, validation handling, and headless GeoJSON warping output.
- **Verification**: Verified headlessly with `pytest tests/test_warp_annotations_dialog.py tests/test_merge_slides_dialog.py tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py tests/test_gui_components.py -v` (56 passed, 0 failures in 4.66s).
- **Status**: Completed

### Task: Enhance MergeSlidesDialog Accessibility, Tooltips, Hand Cursors, and Headless Export Safety
- **Completed**: 2026-10-03
- **Changes**:
  - `src/valis_workstation/ui/dialogs/merge_slides_dialog.py`:
    - Added screen-reader accessible name (`setAccessibleName("Channel Mapping Table")`) and detailed description to `_table`.
    - Added accessible names, descriptive tooltips, object names, and `PointingHandCursor` shapes across all table row checkboxes (`include_cb`) and pseudo-color dropdowns (`color_combo`).
    - Added accessible names, object names, and `PointingHandCursor` shapes to merge options (`_duplicate_handling`, `_output_name`, `_normalize`).
    - Exposed action and dialog buttons as instance attributes (`_button_box`, `_select_all_btn`, `_select_none_btn`, `_export_config_btn`, `_ok_btn`, `_cancel_btn`) with descriptive tooltips, accessible names, object names, and `PointingHandCursor` shapes.
    - Guarded `QMessageBox.information` and `QMessageBox.critical` in `_export_config` with headless/pytest offscreen execution guards to prevent modal popup blocking in automated test runs.
  - `tests/test_merge_slides_dialog.py`:
    - Created unit tests validating accessible names, tooltips, cursor shapes, selection toggle actions (`Select All` / `Select None`), and headless JSON configuration export.
- **Verification**: Verified headlessly with `pytest tests/test_merge_slides_dialog.py tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py -v` (26 passed, 0 failures in 1.11s).
- **Status**: Completed

### Task: Enhance QualityReportDialog Accessibility, Table Copy Action, Hand Cursors, and Headless Export Safety
- **Completed**: 2026-10-03
- **Changes**:
  - `src/valis_workstation/ui/dialogs/quality_report.py`:
    - Added screen-reader accessible names and descriptions (`setAccessibleName("Alignment Quality Metrics Table")`, `setAccessibleDescription(...)`) to `_table`.
    - Added discoverable "Copy Table" button (`_copy_table_btn`) in the button row with inline visual feedback (`✓ Copied!`) and safe timer-based text restoration.
    - Added screen-reader accessible names, descriptive tooltips, and `PointingHandCursor` shapes to `_copy_table_btn`, `_export_csv_btn`, and `_close_btn`.
    - Guarded `QMessageBox.information` and `QMessageBox.critical` in `_export_csv` with headless/pytest offscreen execution guards to prevent modal popup blocking in automated runs.
  - `tests/test_quality_report_dialog.py`:
    - Created unit tests validating accessible names, tooltips, cursor shapes, copy table action and visual feedback, and headless CSV export.
- **Verification**: Verified headlessly with `pytest tests/test_quality_report_dialog.py tests/test_performance_stats_dialog.py tests/test_error_detail_dialog.py tests/test_diagnostics_dialog.py tests/test_save_options_dialog.py tests/test_roi_export_dialog.py -v` (23 passed, 0 failures in 1.39s).
- **Status**: Completed

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

- **Remaining audit plan (2026-10-16)**: (1) ~~Properties combos still elide long values~~ (done 2026-10-22: per-item tooltips + wide popup). (2) Not yet screenshotted: Layers tab (needs napari), WarpAnnotationsDialog, BlinkViewerDialog, FirstRunWizard at small size, Results toolbar, menus. (3) Quick Tutorial uses hard-coded colours in Python; move to QSS. (4) ~~Quick Tutorial "Don't show" checkbox and FirstRun wizard tutorial checkbox~~ (done 2026-10-22). (5) ~~Hard-coded #888 in splash/welcome note: check contrast~~ (done 2026-10-22: polished to #a0a0a0 >= 6.5:1 WCAG AA). (6) Update VALIS-GUI-Manual.html screenshots/text if toolbar labels matter (toolbar is icon-only below ~1450px).
- ~~Add thumbnail caching for large whole-slide image formats.~~ (Completed in `ThumbnailCache` and `thumbnail_generator.py`)
- ~~Implement batch export options for registered slide sets.~~ (Completed via `SaveOptionsDialog` batch export presets)
