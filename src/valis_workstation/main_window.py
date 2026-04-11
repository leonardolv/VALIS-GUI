from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import time
import zipfile
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.constants import ImageFormats
from valis_workstation.layout_constants import (
    CANVAS_MIN_H,
    CANVAS_MIN_W,
    GRID_SPACING,
    LEFT_SIDEBAR_INIT,
    LEFT_SIDEBAR_MAX,
    LEFT_SIDEBAR_MIN,
    RIGHT_SIDEBAR_INIT,
    RIGHT_SIDEBAR_MAX,
    RIGHT_SIDEBAR_MIN,
    SPLITTER_HANDLE_W,
    TIMELINE_INIT_H,
    TIMELINE_MAX_H,
    TIMELINE_MIN_H,
    WINDOW_MIN_H,
    WINDOW_MIN_W,
)
from valis_workstation.models.config import Config
from valis_workstation.services.slide_scan import scan_slide_folder
from valis_workstation.ui import (
    main_window_actions,
    main_window_documents,
    main_window_workflow,
)
from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog
from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog
from valis_workstation.ui.dialogs.diagnostics_dialog import DiagnosticsDialog
from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog
from valis_workstation.ui.dialogs.quality_report import QualityReportDialog
from valis_workstation.ui.dialogs.roi_export_dialog import ROIExportDialog
from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog
from valis_workstation.ui.dialogs.warp_annotations import WarpAnnotationsDialog
from valis_workstation.ui.layer_controls_dock import LayerControlsDock
from valis_workstation.ui.project_dock import ProjectDock
from valis_workstation.ui.properties_dock import PropertiesDock
from valis_workstation.ui.slide_preview_dock import SlidePreviewDock
from valis_workstation.ui.splash_screen import LoadingOverlay
from valis_workstation.ui.splitter_utils import (
    GripSplitter,
    clear_splitter_state,
    collapse_panel,
    persist_splitter_state,
    restore_splitter_state,
)
from valis_workstation.ui.status_dock import StatusDock
from valis_workstation.utils.qt_logging import QtLogEmitter
from valis_workstation.workers.valis_worker import ValisWorker

logger = logging.getLogger(__name__)

# QSettings keys for splitter persistence
_KEY_TOP_SPLITTER = "layout/topSplitter/sizes"
_KEY_OUTER_SPLITTER = "layout/outerSplitter/sizes"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        repo_root: Path,
        log_emitter: QtLogEmitter,
        simple_elastix_available: bool,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo_root = repo_root
        self._log_emitter = log_emitter
        self._worker_thread: QtCore.QThread | None = None
        self._worker: ValisWorker | None = None
        self._merge_thread: QtCore.QThread | None = None
        self._merge_worker: QtCore.QObject | None = None
        self._viewer = None
        self._napari_available = False
        self._last_result: dict | None = None
        self._last_run_context: dict | None = None
        self._current_slide_folder: Path | None = None
        self._last_loaded_config_path: Path | None = None

        self.setWindowTitle("VALIS Workstation")
        self.resize(1400, 900)
        self.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)

        # ── Create panel content holders (docks kept for API compat) ──
        self._project_dock = ProjectDock(self)
        self._properties_dock = PropertiesDock(simple_elastix_available, self)
        self._status_dock = StatusDock(log_emitter, self)
        self._layer_controls_dock: LayerControlsDock | None = None
        self._slide_preview_dock = SlidePreviewDock(self)

        # ── Build splitter-based layout ──────────────────────────────
        self._build_splitter_layout()

        self._build_actions()
        self._setup_keyboard_shortcuts()
        self._setup_status_bar()
        self._restore_window_state()
        self._restore_splitter_state()

        # Enable drag and drop
        self.setAcceptDrops(True)

    # ── Splitter layout construction ─────────────────────────────

    def _build_splitter_layout(self) -> None:
        """Replace dock-widget layout with nested ``QSplitter`` widgets."""

        # -- left panel: tabbed Project + Slide Preview ---------------
        self._left_tabs = QtWidgets.QTabWidget()
        self._left_tabs.setObjectName("LeftPanelTabs")

        left_project_scroll = self._wrap_in_scroll_area(self._project_dock.widget())
        left_preview_scroll = self._wrap_in_scroll_area(
            self._slide_preview_dock.widget()
        )
        self._left_tabs.addTab(left_project_scroll, "Project")
        self._left_tabs.addTab(left_preview_scroll, "Slide Preview")

        left_panel = QtWidgets.QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self._left_tabs)
        left_panel.setMinimumWidth(LEFT_SIDEBAR_MIN)
        left_panel.setMaximumWidth(LEFT_SIDEBAR_MAX)
        left_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        # Prepare right tabs early so central widget can add layer controls
        # when Napari initializes.
        self._right_tabs = QtWidgets.QTabWidget()
        self._right_tabs.setObjectName("RightPanelTabs")

        # -- canvas (centre) ------------------------------------------
        canvas_widget = self._build_central_widget()
        canvas_panel = QtWidgets.QFrame()
        canvas_panel.setObjectName("CanvasPanel")
        canvas_panel.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        canvas_layout = QtWidgets.QVBoxLayout(canvas_panel)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)
        canvas_layout.addWidget(canvas_widget)
        canvas_panel.setMinimumSize(CANVAS_MIN_W, CANVAS_MIN_H)
        canvas_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # -- right panel: tabbed Properties + Layers ------------------
        right_props_scroll = self._wrap_in_scroll_area(self._properties_dock.widget())
        self._right_tabs.addTab(right_props_scroll, "Properties")
        # Layer controls tab is added when napari is ready (see
        # _build_central_widget).  A placeholder is stored so it can be
        # inserted after initialisation.

        right_panel = QtWidgets.QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._right_tabs)
        right_panel.setMinimumWidth(RIGHT_SIDEBAR_MIN)
        right_panel.setMaximumWidth(RIGHT_SIDEBAR_MAX)
        right_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # -- horizontal top splitter: left | canvas | right -----------
        self._top_splitter = GripSplitter(QtCore.Qt.Orientation.Horizontal)
        self._top_splitter.setObjectName("TopSplitter")
        self._top_splitter.setHandleWidth(SPLITTER_HANDLE_W)
        self._top_splitter.setChildrenCollapsible(False)

        self._top_splitter.addWidget(left_panel)
        self._top_splitter.addWidget(canvas_panel)
        self._top_splitter.addWidget(right_panel)

        # Only the canvas absorbs extra space
        self._top_splitter.setStretchFactor(0, 0)
        self._top_splitter.setStretchFactor(1, 1)
        self._top_splitter.setStretchFactor(2, 0)

        for idx in range(self._top_splitter.count()):
            self._top_splitter.setCollapsible(idx, False)

        # -- bottom status panel --------------------------------------
        status_content = self._status_dock.widget()
        status_panel = QtWidgets.QFrame()
        status_panel.setObjectName("StatusPanel")
        status_panel.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        status_layout = QtWidgets.QVBoxLayout(status_panel)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)
        status_layout.addWidget(status_content)
        status_panel.setMinimumHeight(TIMELINE_MIN_H)
        status_panel.setMaximumHeight(TIMELINE_MAX_H)

        # -- outer vertical splitter: top | status --------------------
        self._outer_splitter = GripSplitter(QtCore.Qt.Orientation.Vertical)
        self._outer_splitter.setObjectName("OuterSplitter")
        self._outer_splitter.setHandleWidth(SPLITTER_HANDLE_W)
        self._outer_splitter.setChildrenCollapsible(False)

        self._outer_splitter.addWidget(self._top_splitter)
        self._outer_splitter.addWidget(status_panel)

        # Top area absorbs extra vertical space
        self._outer_splitter.setStretchFactor(0, 1)
        self._outer_splitter.setStretchFactor(1, 0)

        for idx in range(self._outer_splitter.count()):
            self._outer_splitter.setCollapsible(idx, False)

        # -- initial sizes --------------------------------------------
        canvas_init = max(
            CANVAS_MIN_W,
            self.width()
            - LEFT_SIDEBAR_INIT
            - RIGHT_SIDEBAR_INIT
            - 2 * SPLITTER_HANDLE_W,
        )
        self._top_splitter.setSizes(
            [LEFT_SIDEBAR_INIT, canvas_init, RIGHT_SIDEBAR_INIT]
        )
        main_area_h = max(
            CANVAS_MIN_H, self.height() - TIMELINE_INIT_H - SPLITTER_HANDLE_W
        )
        self._outer_splitter.setSizes([main_area_h, TIMELINE_INIT_H])

        # -- connect splitter-moved to auto-persist -------------------
        self._top_splitter.splitterMoved.connect(
            lambda: persist_splitter_state(self._top_splitter, _KEY_TOP_SPLITTER)
        )
        self._outer_splitter.splitterMoved.connect(
            lambda: persist_splitter_state(self._outer_splitter, _KEY_OUTER_SPLITTER)
        )

        # -- set as central widget ------------------------------------
        self.setCentralWidget(self._outer_splitter)

        # Keep panel references for programmatic helpers
        self._left_panel = left_panel
        self._canvas_panel = canvas_panel
        self._right_panel = right_panel
        self._status_panel = status_panel

    # ── Scroll-area wrapper ──────────────────────────────────────

    @staticmethod
    def _wrap_in_scroll_area(widget: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        """Wrap *widget* in a ``QScrollArea`` with ``widgetResizable``."""
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        return scroll

    def _build_central_widget(self) -> QtWidgets.QWidget:
        napari_spec = importlib.util.find_spec("napari")
        if napari_spec is None:
            return self._napari_unavailable_widget()

        napari_module = importlib.import_module("napari")
        try:
            self._viewer = napari_module.Viewer(show=False)
            self._napari_available = True
            logger.info("Napari viewer initialized successfully")

            # Add layer controls as a tab in the right panel
            self._layer_controls_dock = LayerControlsDock(self._viewer, self)
            layer_widget = self._layer_controls_dock.widget()
            if layer_widget is not None:
                layer_scroll = self._wrap_in_scroll_area(layer_widget)
                self._right_tabs.addTab(layer_scroll, "Layers")
        except Exception:
            logger.exception("Failed to start napari viewer")
            return self._napari_unavailable_widget()

        return self._viewer.window._qt_window

    def _napari_unavailable_widget(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        title = QtWidgets.QLabel("<h2>Napari Viewer Not Available</h2>")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        message = QtWidgets.QLabel(
            "<p>The Napari image viewer could not be initialized.</p>"
            "<p>To install Napari, run:</p>"
            "<p style='font-family: monospace; background: #3b3b3b; padding: 10px;'>"
            "pip install napari[all]</p>"
            "<p>Then restart the application.</p>"
            "<p style='color: #888;'><i>You can still use other features like registration,</i></p>"
            "<p style='color: #888;'><i>but visualization will be limited.</i></p>"
        )
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()

        return widget

    def _build_actions(self) -> None:
        main_window_actions.build_actions(self)

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common operations."""
        main_window_actions.setup_keyboard_shortcuts(self)

        logger.debug("Keyboard shortcuts configured")

    def _setup_status_bar(self) -> None:
        """Setup status bar at the bottom of the window."""
        self._status_bar = self.statusBar()
        self._status_bar.showMessage("Ready")
        logger.debug("Status bar configured")

    def _open_slide_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Slide Folder")
        if not folder:
            return
        self._load_slides_from_folder(Path(folder))

    def _start_registration(self) -> None:
        main_window_workflow.start_registration(self)

    def _start_registration_from_context(self, context: dict) -> None:
        """Start worker from a stored run context (new run or resume)."""
        main_window_workflow.start_registration_from_context(self, context)

    def _resume_last_registration(self) -> None:
        """Resume/re-run the last registration context after cancel/failure."""
        main_window_workflow.resume_last_registration(self)

    def _cleanup_worker(self) -> None:
        main_window_workflow.cleanup_worker(self)

    def _request_cancellation(self) -> None:
        """Handle user request to cancel registration."""
        main_window_workflow.request_cancellation(self)

    def _on_worker_cancelled(self) -> None:
        """Handle worker cancellation."""
        main_window_workflow.on_worker_cancelled(self)

    def _confirm_registration(self, slides: list[Path], output_dir: Path) -> bool:
        """Show one confirmation dialog with estimates and settings."""
        return main_window_workflow.confirm_registration(self, slides, output_dir)

    @staticmethod
    def _safe_total_size_bytes(slides: list[Path]) -> tuple[int, bool]:
        return main_window_workflow.safe_total_size_bytes(slides)

    def _on_worker_finished(self, result: dict) -> None:
        main_window_workflow.on_worker_finished(self, result)

    def _on_worker_failed(self, message: str) -> None:
        main_window_workflow.on_worker_failed(self, message)

    def _blink(self) -> None:
        if not self._napari_available or self._viewer is None:
            QtWidgets.QMessageBox.warning(self, "Blink", "Napari not available.")
            return
        if not self._last_result or not self._last_result.get("registered_dir"):
            QtWidgets.QMessageBox.warning(
                self, "Blink", "No registered slides available."
            )
            return
        registered_dir = Path(self._last_result["registered_dir"])
        slide_paths = sorted(registered_dir.glob("*.ome.tiff"))
        if len(slide_paths) < 2:
            QtWidgets.QMessageBox.warning(
                self, "Blink", "Need at least two registered slides."
            )
            return
        dialog = BlinkViewerDialog(self._viewer, slide_paths, self)
        dialog.exec()

    def _show_analysis_plot(self) -> None:
        if not self._last_result or "summary_df" not in self._last_result:
            QtWidgets.QMessageBox.warning(self, "Analysis", "No results available.")
            return
        logger.info("Opening analysis plot dialog")
        summary_df = self._last_result["summary_df"]
        dialog = AnalysisPlotDialog(summary_df, self)
        dialog.exec()

    def _show_quality_report(self) -> None:
        if not self._last_result or "summary_df" not in self._last_result:
            QtWidgets.QMessageBox.warning(
                self, "Quality Report", "No results available."
            )
            return
        logger.info("Opening quality report dialog")
        summary_df = self._last_result["summary_df"]
        dialog = QualityReportDialog(summary_df, self)
        dialog.exec()

    def _warp_annotations(self) -> None:
        if not self._last_result or "registrar" not in self._last_result:
            QtWidgets.QMessageBox.warning(
                self, "Warp", "No registration results available."
            )
            return
        output_dir = Path(self._last_result["output_dir"])
        dialog = WarpAnnotationsDialog(self._last_result["registrar"], output_dir, self)
        dialog.exec()

    def _load_registered_layers(self, result: dict) -> None:
        if not self._napari_available or self._viewer is None:
            return

        progress = QtWidgets.QProgressDialog(
            "Loading registered output into viewer...", "Abort", 0, 0, self
        )
        progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        progress.show()

        registered_dir = Path(result["registered_dir"])
        for layer in list(self._viewer.layers):
            if layer.name.startswith("Registered:"):
                self._viewer.layers.remove(layer)

        slides = list(sorted(registered_dir.glob("*.ome.tiff")))
        progress.setMaximum(len(slides))

        for i, slide_path in enumerate(slides):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            progress.setLabelText(f"Loading: {slide_path.name}...")
            QtWidgets.QApplication.processEvents()

            try:
                layer_result = self._viewer.open(
                    str(slide_path), name=f"Registered: {slide_path.name}"
                )
                if isinstance(layer_result, list):
                    for layer in layer_result:
                        layer.name = f"Registered: {layer.name}"
            except Exception:
                logger.exception("Failed to load registered slide %s", slide_path)

        progress.setValue(len(slides))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event with proper resource cleanup."""
        logger.info("Closing main window - initiating cleanup")

        # Save window state and splitter layout
        self._save_window_state()
        self._save_splitter_state()

        # Stop and cleanup worker thread if running
        if self._worker_thread and self._worker_thread.isRunning():
            logger.warning("Worker thread still running - requesting termination")

            # Try to cancel the worker first
            if self._worker:
                self._worker.cancel()

            # Give it time to finish gracefully
            self._worker_thread.quit()
            if not self._worker_thread.wait(2000):  # Wait max 2 seconds
                logger.error(
                    "Worker thread did not terminate gracefully, forcing termination"
                )
                self._worker_thread.terminate()
                self._worker_thread.wait(500)

        # Stop and cleanup merge thread if running
        if self._merge_thread and self._merge_thread.isRunning():
            logger.warning("Merge thread still running - requesting termination")

            cancel_fn = None
            if self._merge_worker is not None:
                cancel_fn = getattr(self._merge_worker, "cancel", None)
            if callable(cancel_fn):
                cancel_fn()

            self._merge_thread.quit()
            if not self._merge_thread.wait(2000):
                logger.error(
                    "Merge thread did not terminate gracefully, forcing termination"
                )
                self._merge_thread.terminate()
                self._merge_thread.wait(500)

        # Cleanup napari viewer
        if self._viewer is not None:
            try:
                logger.info("Closing napari viewer")
                self._viewer.close()
                self._viewer = None
            except Exception as e:
                logger.exception("Failed to close napari viewer: %s", e)

        # Clear references to help garbage collection
        self._worker = None
        self._worker_thread = None
        self._merge_worker = None
        self._merge_thread = None
        self._last_result = None

        logger.info("Cleanup complete, closing application")
        super().closeEvent(event)

    def _save_window_state(self) -> None:
        """Save window geometry and dock states to QSettings."""
        settings = QtCore.QSettings("VALIS", "Workstation")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        logger.debug("Window state saved")

    def _restore_window_state(self) -> None:
        """Restore window geometry and dock states from QSettings."""
        settings = QtCore.QSettings("VALIS", "Workstation")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            logger.debug("Window geometry restored")
        window_state = settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            logger.debug("Window state restored")

    # ── Splitter persistence ─────────────────────────────────────

    def _save_splitter_state(self) -> None:
        """Persist both splitter size lists to QSettings."""
        persist_splitter_state(self._top_splitter, _KEY_TOP_SPLITTER)
        persist_splitter_state(self._outer_splitter, _KEY_OUTER_SPLITTER)
        logger.debug("Splitter state saved")

    def _restore_splitter_state(self) -> None:
        """Restore splitter sizes from QSettings, falling back to defaults."""
        canvas_init = max(
            CANVAS_MIN_W,
            self.width()
            - LEFT_SIDEBAR_INIT
            - RIGHT_SIDEBAR_INIT
            - 2 * SPLITTER_HANDLE_W,
        )
        restore_splitter_state(
            self._top_splitter,
            _KEY_TOP_SPLITTER,
            default_sizes=[LEFT_SIDEBAR_INIT, canvas_init, RIGHT_SIDEBAR_INIT],
        )
        main_area_h = max(
            CANVAS_MIN_H,
            self.height() - TIMELINE_INIT_H - SPLITTER_HANDLE_W,
        )
        restore_splitter_state(
            self._outer_splitter,
            _KEY_OUTER_SPLITTER,
            default_sizes=[main_area_h, TIMELINE_INIT_H],
        )

    # ── Programmatic layout helpers ──────────────────────────────

    def _update_tools_enabled(self) -> None:
        """Enable/disable Tools menu actions based on whether results exist."""
        has_result = self._last_result is not None
        for action in getattr(self, "_result_actions", []):
            action.setEnabled(has_result)

    def reset_layout(self) -> None:
        """Reset splitters to default sizes."""
        canvas_init = max(
            CANVAS_MIN_W,
            self.width()
            - LEFT_SIDEBAR_INIT
            - RIGHT_SIDEBAR_INIT
            - 2 * SPLITTER_HANDLE_W,
        )
        self._top_splitter.setSizes(
            [LEFT_SIDEBAR_INIT, canvas_init, RIGHT_SIDEBAR_INIT]
        )
        main_area_h = max(
            CANVAS_MIN_H,
            self.height() - TIMELINE_INIT_H - SPLITTER_HANDLE_W,
        )
        self._outer_splitter.setSizes([main_area_h, TIMELINE_INIT_H])

        # Clear persisted state so next launch also uses defaults
        clear_splitter_state(_KEY_TOP_SPLITTER)
        clear_splitter_state(_KEY_OUTER_SPLITTER)
        logger.info("Layout reset to defaults")
        self._status_bar.showMessage("Layout reset to defaults", 3000)

    def toggle_left_sidebar(self) -> None:
        """Collapse or restore the left sidebar."""
        sizes = self._top_splitter.sizes()
        if sizes[0] > LEFT_SIDEBAR_MIN:
            collapse_panel(self._top_splitter, 0, LEFT_SIDEBAR_MIN)
        else:
            old_size = sizes[0]
            sizes[0] = LEFT_SIDEBAR_INIT
            sizes[1] = max(CANVAS_MIN_W, sizes[1] - (LEFT_SIDEBAR_INIT - old_size))
            self._top_splitter.setSizes(sizes)

    def toggle_right_sidebar(self) -> None:
        """Collapse or restore the right sidebar."""
        sizes = self._top_splitter.sizes()
        if sizes[2] > RIGHT_SIDEBAR_MIN:
            collapse_panel(self._top_splitter, 2, RIGHT_SIDEBAR_MIN)
        else:
            old_size = sizes[2]
            sizes[2] = RIGHT_SIDEBAR_INIT
            sizes[1] = max(CANVAS_MIN_W, sizes[1] - (RIGHT_SIDEBAR_INIT - old_size))
            self._top_splitter.setSizes(sizes)

    def expand_center(self) -> None:
        """Minimise both sidebars so the canvas gets maximum space."""
        total = sum(self._top_splitter.sizes())
        center = total - LEFT_SIDEBAR_MIN - RIGHT_SIDEBAR_MIN
        self._top_splitter.setSizes([LEFT_SIDEBAR_MIN, center, RIGHT_SIDEBAR_MIN])
        logger.debug("Center panel expanded")

    def fit_to_content(self) -> None:
        """Resize timeline to its preferred height."""
        self._outer_splitter.setSizes(
            [self.height() - TIMELINE_INIT_H - SPLITTER_HANDLE_W, TIMELINE_INIT_H]
        )

    def _open_repo_document(
        self, relative_name: str, title: str, log_label: str
    ) -> None:
        """Open a repository document in the default browser with a unified fallback."""
        main_window_documents.open_repo_document(self, relative_name, title, log_label)

    def _open_user_manual(self) -> None:
        """Open the HTML manual in the default browser."""
        main_window_documents.open_user_manual(self)

    def _open_tutorial(self) -> None:
        """Open the HTML tutorial in the default browser."""
        main_window_documents.open_tutorial(self)

    def _open_quick_start(self) -> None:
        """Open the quick start guide in default browser."""
        main_window_documents.open_quick_start(self)

    def _report_issue(self) -> None:
        """Open GitHub issue page."""
        main_window_documents.report_issue(self)

    def _show_about(self) -> None:
        """Show About dialog."""
        main_window_documents.show_about(self)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept drag events containing file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            logger.debug("Drag enter accepted")

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handle dropped files/folders."""
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                logger.info("Dropped folder: %s", path)
                self._load_slides_from_folder(path)
                break  # Only process first folder
            elif path.is_file():
                # Check if it's a config file
                if path.suffix.lower() == ".json":
                    logger.info("Dropped config file: %s", path)
                    self._load_config_from_path(path)
                    break
        event.acceptProposedAction()

    def _load_slides_from_folder(self, folder: Path) -> None:
        """Load slides from a folder path."""
        overlay = LoadingOverlay(self, f"Scanning {folder.name}…")
        overlay.set_stage("Scan")
        overlay.set_progress(5)
        overlay.show()
        QtWidgets.QApplication.processEvents()
        try:
            slides = scan_slide_folder(folder)
            overlay.set_progress(30)
            if slides:
                self._current_slide_folder = folder
                self._project_dock.set_slides(slides)
                self._add_to_recent_folders(str(folder))

                # Update reference slide list in properties dock
                slide_names = [s.stem for s in slides]
                self._properties_dock.update_reference_slide_list(slide_names)

                # Update slide preview dock with real thumbnails (parallel loading)
                overlay.set_stage("Thumbnail")
                overlay.set_message(f"Generating thumbnails for {len(slides)} slides…")
                QtWidgets.QApplication.processEvents()
                self._slide_preview_dock.clear()
                self._load_thumbnails_parallel(slides, overlay)
                overlay.set_progress(100)

                # Auto-load associated config if one was linked to this folder.
                linked_cfg = self._get_recent_folder_config(folder)
                if linked_cfg and linked_cfg.exists():
                    self._load_config_from_path(linked_cfg)

                logger.info("Loaded %d slides from %s", len(slides), folder.name)
                self._status_bar.showMessage(
                    f"Loaded {len(slides)} slides from {folder.name}"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Slides Found",
                    f"No supported slide images found in {folder.name}",
                )
        except Exception as e:
            logger.exception("Failed to load slides from %s", folder)
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to load slides from {folder.name}:\n{str(e)}"
            )
        finally:
            overlay.dismiss()

    def _load_thumbnails_parallel(
        self, slides: list[Path], overlay: LoadingOverlay | None = None
    ) -> None:
        """Load thumbnails in parallel using thread pool.

        Parameters
        ----------
        slides : list[Path]
            List of slide file paths to generate thumbnails for
        overlay : LoadingOverlay | None
            Optional overlay to update with progress messages
        """
        import concurrent.futures

        from valis_workstation.services.thumbnail_generator import generate_thumbnail

        total_slides = len(slides)
        completed = 0
        started_at = time.time()

        # Update status bar
        self._status_bar.showMessage(f"Generating thumbnails: 0/{total_slides}")

        def generate_and_update(
            slide_path: Path,
        ) -> tuple[str, QtGui.QPixmap | None, dict]:
            """Generate thumbnail and return results."""
            try:
                thumbnail, metadata = generate_thumbnail(slide_path, max_size=512)
                return slide_path.stem, thumbnail, metadata
            except Exception as e:
                logger.warning(
                    "Failed to generate thumbnail for %s: %s", slide_path.name, e
                )
                return slide_path.stem, None, {"file_path": str(slide_path)}

        # Use ThreadPoolExecutor with limited workers to avoid overwhelming disk I/O
        # 4 workers is a good balance for I/O bound operations
        max_workers = min(4, total_slides)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_slide = {
                executor.submit(generate_and_update, slide): slide for slide in slides
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_slide):
                slide_name, thumbnail, metadata = future.result()

                # Add to preview dock
                self._slide_preview_dock.add_slide(slide_name, thumbnail, metadata)

                # Update progress
                completed += 1
                msg = f"Generating thumbnails: {completed}/{total_slides}"
                self._status_bar.showMessage(msg)
                if overlay is not None:
                    overlay.set_stage("Thumbnail")
                    overlay.set_message(msg)
                    overlay.set_progress(completed, total_slides)
                    elapsed = max(0.001, time.time() - started_at)
                    rate = completed / elapsed
                    remaining = (total_slides - completed) / rate if rate > 0 else None
                    overlay.set_eta_seconds(remaining)

                # Process events to keep UI responsive
                QtWidgets.QApplication.processEvents()

        logger.info("Generated %d/%d thumbnails", completed, total_slides)

    def _add_to_recent_folders(self, folder_path: str) -> None:
        """Add folder to recent folders list."""
        settings = QtCore.QSettings("VALIS", "Workstation")
        recent = settings.value("recent_folders", [])

        if not isinstance(recent, list):
            recent = []

        # Remove if already exists
        if folder_path in recent:
            recent.remove(folder_path)

        # Add to front
        recent.insert(0, folder_path)

        # Keep only last 10
        recent = recent[:10]

        settings.setValue("recent_folders", recent)
        self._update_recent_folders_menu()
        logger.debug("Added %s to recent folders", folder_path)

    def _save_recent_folder_config(self, folder: Path, config_path: Path) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        raw = settings.value("recent_folder_configs", "{}")
        try:
            mapping = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except Exception:
            mapping = {}
        mapping[str(folder)] = str(config_path)
        settings.setValue("recent_folder_configs", json.dumps(mapping))

    def _get_recent_folder_config(self, folder: Path) -> Path | None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        raw = settings.value("recent_folder_configs", "{}")
        try:
            mapping = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except Exception:
            mapping = {}
        path = mapping.get(str(folder))
        return Path(path) if path else None

    def _open_recent_with_config(self, folder: Path) -> None:
        # `_load_slides_from_folder` already auto-loads linked configs.
        self._load_slides_from_folder(folder)

    def _update_recent_folders_menu(self) -> None:
        """Update the recent folders menu."""
        self._recent_menu.clear()
        settings = QtCore.QSettings("VALIS", "Workstation")
        recent = settings.value("recent_folders", [])

        if not isinstance(recent, list):
            recent = []

        if not recent:
            action = self._recent_menu.addAction("(No recent folders)")
            action.setEnabled(False)
        else:
            for folder_path in recent:
                path = Path(folder_path)
                exists = path.exists()
                label = path.name if exists else f"[missing] {path.name}"
                action = self._recent_menu.addAction(label)
                action.setToolTip(folder_path)
                action.setEnabled(exists)
                action.triggered.connect(
                    lambda checked=False, p=path: self._load_slides_from_folder(p)
                )
                cfg = self._get_recent_folder_config(path)
                if cfg is not None:
                    cfg_action = self._recent_menu.addAction(
                        f"  -> Open with config ({cfg.name})"
                    )
                    cfg_action.setEnabled(exists and cfg.exists())
                    cfg_action.setToolTip(f"Folder: {folder_path}\nConfig: {cfg}")
                    cfg_action.triggered.connect(
                        lambda checked=False, p=path: self._open_recent_with_config(p)
                    )

    def _save_configuration(self) -> None:
        """Save current configuration to JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            str(self._repo_root / "configs"),
            "JSON Files (*.json)",
        )

        if not file_path:
            return

        try:
            import dataclasses
            import json

            config = self._properties_dock.config()
            config_dict = dataclasses.asdict(config)

            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            self._last_loaded_config_path = Path(file_path)
            if self._current_slide_folder is not None:
                self._save_recent_folder_config(
                    self._current_slide_folder, Path(file_path)
                )

            logger.info("Saved configuration to %s", file_path)
            self._status_bar.showMessage(
                f"Configuration saved to {Path(file_path).name}", 3000
            )
        except Exception as e:
            logger.exception("Failed to save configuration")
            QtWidgets.QMessageBox.critical(
                self, "Save Error", f"Failed to save configuration:\n{e}"
            )

    def _load_configuration(self) -> None:
        """Load configuration from JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            str(self._repo_root / "configs"),
            "JSON Files (*.json)",
        )

        if not file_path:
            return

        self._load_config_from_path(Path(file_path))

    def _load_config_from_path(self, file_path: Path) -> None:
        """Load configuration from a JSON file and populate the dock."""
        try:
            import json

            with open(file_path, "r") as f:
                config_dict = json.load(f)

            # Build a Config from the dict, falling back to defaults for
            # any keys that are missing (e.g. older config files).
            cfg = Config(
                **{
                    k: v
                    for k, v in config_dict.items()
                    if k in Config.__dataclass_fields__
                }
            )

            self._properties_dock.set_config(cfg)
            self._last_loaded_config_path = file_path
            if self._current_slide_folder is not None:
                self._save_recent_folder_config(self._current_slide_folder, file_path)

            logger.info("Loaded configuration from %s", file_path)
            self._status_bar.showMessage(
                f"Configuration loaded from {file_path.name}", 3000
            )
        except Exception as e:
            logger.exception("Failed to load configuration")
            QtWidgets.QMessageBox.critical(
                self, "Load Error", f"Failed to load configuration:\n{e}"
            )

    def _show_save_options(self) -> None:
        """Show save-options dialog and copy results into the Properties dock."""
        dialog = SaveOptionsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            options = dialog.get_options()
            logger.info("Save options configured: %s", options)

            # Push values into the Properties dock so they flow into Config
            dock = self._properties_dock
            if "pyramid_levels" in options:
                dock._pyramid_levels_spin.setValue(int(options["pyramid_levels"]))
            if "compression" in options:
                dock._compression_level_spin.setValue(int(options["compression"]))
            if "tile_size" in options:
                dock._tile_size_spin.setValue(int(options["tile_size"]))
            if "quality" in options:
                dock._image_quality_spin.setValue(int(options["quality"]))

            # Ensure the Output Settings group is visible
            dock._output_group.setChecked(True)

            self._status_bar.showMessage("Output settings updated", 5000)

    def _merge_slides(self) -> None:
        """Show merge slides dialog for creating multi-channel images."""
        if not self._last_result or "registrar" not in self._last_result:
            QtWidgets.QMessageBox.warning(
                self,
                "Merge Slides",
                "No registered slides available. Please run registration first.",
            )
            return

        if self._merge_thread and self._merge_thread.isRunning():
            QtWidgets.QMessageBox.information(
                self,
                "Merge Slides",
                "A merge is already running. Please wait for it to finish.",
            )
            return

        # Get list of slide names from the registrar
        registrar = self._last_result["registrar"]
        slide_names = [slide.name for slide in registrar.slide_dict.values()]

        if len(slide_names) < 2:
            QtWidgets.QMessageBox.warning(
                self, "Merge Slides", "Need at least 2 registered slides to merge."
            )
            return

        dialog = MergeSlidesDialog(slide_names, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            merge_config = dialog.get_merge_config()
            logger.info("Merge configuration: %s", merge_config)

            if not merge_config["channels"]:
                QtWidgets.QMessageBox.warning(
                    self, "Merge Slides", "No channels selected for merging."
                )
                return

            # Get output directory and save config
            output_dir = Path(self._last_result["output_dir"])
            config = self._properties_dock.config()
            save_config = {
                "pyramid_levels": config.pyramid_levels,
                "compression_level": config.compression_level,
                "tile_size": config.tile_size,
                "image_quality": config.image_quality,
            }

            # Run merge in a background thread
            from valis_workstation.services.merge_slides import merge_registered_slides

            self._status_bar.showMessage(
                f"Merging {len(merge_config['channels'])} channels...", 0
            )

            self._merge_thread = QtCore.QThread(self)

            class _MergeWorker(QtCore.QObject):
                finished = QtCore.Signal(object)
                failed = QtCore.Signal(str)

                def __init__(self, registrar, merge_config, output_dir, save_config):
                    super().__init__()
                    self._registrar = registrar
                    self._merge_config = merge_config
                    self._output_dir = output_dir
                    self._save_config = save_config
                    self._cancel_requested = False

                def cancel(self):
                    self._cancel_requested = True

                def run(self):
                    try:
                        result_path = merge_registered_slides(
                            registrar=self._registrar,
                            merge_config=self._merge_config,
                            output_path=self._output_dir,
                            save_config=self._save_config,
                            progress_callback=None,
                            cancel_check=lambda: self._cancel_requested,
                        )
                        self.finished.emit(result_path)
                    except Exception as exc:
                        self.failed.emit(str(exc))

            self._merge_worker = _MergeWorker(
                registrar, merge_config, output_dir, save_config
            )
            merge_thread = self._merge_thread
            merge_worker = self._merge_worker
            merge_worker.moveToThread(merge_thread)

            def cleanup_merge_resources() -> None:
                merge_worker.deleteLater()
                merge_thread.deleteLater()
                if self._merge_worker is merge_worker:
                    self._merge_worker = None
                if self._merge_thread is merge_thread:
                    self._merge_thread = None

            def on_merge_success(result_path):
                logger.info("Merge completed: %s", result_path)
                self._status_bar.showMessage(f"Slides merged successfully", 5000)
                QtWidgets.QMessageBox.information(
                    self,
                    "Merge Complete",
                    f"Successfully merged {len(merge_config['channels'])} channels.\n\n"
                    f"Output: {result_path}",
                )

            def on_merge_error(msg):
                logger.error("Merge failed: %s", msg)
                self._status_bar.showMessage("Merge failed", 5000)
                QtWidgets.QMessageBox.critical(
                    self, "Merge Failed", f"Failed to merge slides:\n{msg}"
                )

            merge_worker.finished.connect(on_merge_success)
            merge_worker.failed.connect(on_merge_error)
            merge_worker.finished.connect(merge_thread.quit)
            merge_worker.failed.connect(merge_thread.quit)
            merge_thread.finished.connect(cleanup_merge_resources)
            merge_thread.started.connect(merge_worker.run)
            merge_thread.start()

    def _export_roi_crop(self) -> None:
        """Show ROI export dialog and process the crop across all registered slides."""
        if not self._last_result or "registrar" not in self._last_result:
            QtWidgets.QMessageBox.warning(
                self, "Export ROI", "No registered slides available."
            )
            return

        dialog = ROIExportDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            options = dialog.get_options()
            bbox = options["bbox"]  # (x, y, w, h)
            fmt = options["format"]
            reopen = options["reopen"]

            # Request directory to save crops to
            out_dir = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory for ROI Crops", str(Path.home())
            )
            if not out_dir:
                return

            out_path = Path(out_dir)

            registrar = self._last_result["registrar"]
            from valis import warp_tools

            self._status_bar.showMessage("Extracting ROIs...")
            QtWidgets.QApplication.processEvents()
            try:
                # Provide a visible progress
                progress = QtWidgets.QProgressDialog(
                    "Exporting ROIs...", "Cancel", 0, len(registrar.slide_dict), self
                )
                progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

                new_slide_files = []
                # Map standard formats
                ext = ".tiff"
                if fmt == ImageFormats.OME_TIFF:
                    ext = ".ome.tiff"
                elif fmt == ImageFormats.PNG:
                    ext = ".png"

                i = 0
                for slide_name, slide_obj in registrar.slide_dict.items():
                    if progress.wasCanceled():
                        break

                    progress.setValue(i)
                    progress.setLabelText(f"Exporting ROI for {slide_name}...")

                    warped_slide = slide_obj.warp_slide(level=0)
                    roi_vips = warped_slide.extract_area(*bbox)

                    out_file = out_path / f"{slide_name}_ROI{ext}"
                    # convert properly
                    warp_tools.save_img(str(out_file), roi_vips)
                    new_slide_files.append(str(out_file))

                    i += 1
                progress.setValue(len(registrar.slide_dict))

                QtWidgets.QMessageBox.information(
                    self,
                    "ROI Export",
                    f"Successfully exported {len(new_slide_files)} ROIs to:\n{out_path}",
                )

                if (
                    reopen
                    and new_slide_files
                    and self._napari_available
                    and self._viewer
                ):
                    for sf in new_slide_files:
                        self._viewer.open(sf)

            except Exception as e:
                logger.exception("Failed to export ROI")
                QtWidgets.QMessageBox.critical(self, "Export Failed", str(e))

            self._status_bar.showMessage("ROI Export finished", 5000)

    def _export_session_bundle(self) -> None:
        """Export config + logs + diagnostics summary into a zip bundle."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = str(self._repo_root / "logs" / f"session_bundle_{ts}.zip")
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Session Bundle",
            default_name,
            "ZIP Files (*.zip)",
        )
        if not out_path:
            return

        try:
            cfg = self._properties_dock.config()
            payload = {
                "timestamp": ts,
                "config": cfg.__dict__,
                "current_slide_folder": str(self._current_slide_folder)
                if self._current_slide_folder
                else None,
                "last_result": self._last_result,
            }
            with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "session_summary.json", json.dumps(payload, indent=2, default=str)
                )
                log_file = self._repo_root / "logs" / "valis_workstation.log"
                if log_file.exists():
                    zf.write(log_file, arcname="valis_workstation.log")
            QtWidgets.QMessageBox.information(
                self, "Export", f"Session bundle exported to:\n{out_path}"
            )
        except Exception as exc:
            logger.exception("Failed to export session bundle")
            QtWidgets.QMessageBox.critical(self, "Export Failed", str(exc))

    def _show_diagnostics(self) -> None:
        dialog = DiagnosticsDialog(self._repo_root, self._last_result, self)
        dialog.exec()

    def _show_performance_stats(self) -> None:
        """Show the performance statistics dialog."""
        from valis_workstation.ui.dialogs.performance_stats_dialog import (
            PerformanceStatsDialog,
        )

        dialog = PerformanceStatsDialog(self)
        dialog.exec()

        logger.info("Performance statistics dialog opened")

    def _show_preferences(self) -> None:
        """Show the preferences dialog."""
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(self)
        dialog.preferences_changed.connect(self._on_preferences_changed)
        dialog.exec()

        logger.info("Preferences dialog opened")

    def _on_preferences_changed(self) -> None:
        """Handle preferences changes."""
        logger.info("Preferences changed - some settings require application restart")

        QtWidgets.QMessageBox.information(
            self,
            "Preferences Saved",
            "Some preference changes require restarting the application to take effect.",
        )
