from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.models.config import Config
from valis_workstation.services.slide_scan import scan_slide_folder
from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog
from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog
from valis_workstation.ui.dialogs.error_detail_dialog import show_error_dialog
from valis_workstation.ui.dialogs.quality_report import QualityReportDialog
from valis_workstation.ui.dialogs.warp_annotations import WarpAnnotationsDialog
from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog
from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog
from valis_workstation.ui.layer_controls_dock import LayerControlsDock
from valis_workstation.ui.project_dock import ProjectDock
from valis_workstation.ui.properties_dock import PropertiesDock
from valis_workstation.ui.slide_preview_dock import SlidePreviewDock
from valis_workstation.ui.status_dock import StatusDock
from valis_workstation.utils.qt_logging import QtLogEmitter
from valis_workstation.utils.validation import validate_slides
from valis_workstation.workers.valis_worker import ValisWorker

logger = logging.getLogger(__name__)


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
        self._viewer = None
        self._napari_available = False
        self._last_result: dict | None = None

        self.setWindowTitle("VALIS Workstation")
        self.resize(1400, 900)

        self._project_dock = ProjectDock(self)
        self._properties_dock = PropertiesDock(simple_elastix_available, self)
        self._status_dock = StatusDock(log_emitter, self)
        self._layer_controls_dock: LayerControlsDock | None = None
        self._slide_preview_dock = SlidePreviewDock(self)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._project_dock)
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self._properties_dock
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self._status_dock
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._slide_preview_dock
        )
        self.tabifyDockWidget(self._project_dock, self._slide_preview_dock)

        self.setCentralWidget(self._build_central_widget())
        self._build_actions()
        self._setup_keyboard_shortcuts()
        self._setup_status_bar()
        self._restore_window_state()
        
        # Enable drag and drop
        self.setAcceptDrops(True)

    def _build_central_widget(self) -> QtWidgets.QWidget:
        napari_spec = importlib.util.find_spec("napari")
        if napari_spec is None:
            return self._napari_unavailable_widget()

        napari_module = importlib.import_module("napari")
        try:
            self._viewer = napari_module.Viewer(show=False)
            self._napari_available = True
            logger.info("Napari viewer initialized successfully")
            
            # Add layer controls dock for napari
            self._layer_controls_dock = LayerControlsDock(self._viewer, self)
            self.addDockWidget(
                QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self._layer_controls_dock
            )
            self.tabifyDockWidget(self._properties_dock, self._layer_controls_dock)
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
        style = self.style()
        
        file_menu = self.menuBar().addMenu("File")
        
        open_action = QtGui.QAction("Open Slide Folder", self)
        open_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon))
        open_action.triggered.connect(self._open_slide_folder)
        file_menu.addAction(open_action)
        
        # Recent folders submenu
        self._recent_menu = file_menu.addMenu("Recent Folders")
        self._recent_menu.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self._update_recent_folders_menu()
        
        file_menu.addSeparator()
        
        save_config_action = QtGui.QAction("Save Configuration...", self)
        save_config_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
        save_config_action.triggered.connect(self._save_configuration)
        file_menu.addAction(save_config_action)
        
        load_config_action = QtGui.QAction("Load Configuration...", self)
        load_config_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton))
        load_config_action.triggered.connect(self._load_configuration)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()

        run_action = QtGui.QAction("Run Registration", self)
        run_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        run_action.triggered.connect(self._start_registration)
        file_menu.addAction(run_action)
        
        file_menu.addSeparator()
        
        preferences_action = QtGui.QAction("Preferences...", self)
        preferences_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self._show_preferences)
        file_menu.addAction(preferences_action)

        tools_menu = self.menuBar().addMenu("Tools")
        
        blink_action = QtGui.QAction("Blink", self)
        blink_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        blink_action.triggered.connect(self._blink)
        tools_menu.addAction(blink_action)

        plot_action = QtGui.QAction("Analysis Plot", self)
        plot_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView))
        plot_action.triggered.connect(self._show_analysis_plot)
        tools_menu.addAction(plot_action)

        quality_action = QtGui.QAction("Quality Report", self)
        quality_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView))
        quality_action.triggered.connect(self._show_quality_report)
        tools_menu.addAction(quality_action)

        warp_action = QtGui.QAction("Warp Annotations", self)
        warp_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView))
        warp_action.triggered.connect(self._warp_annotations)
        tools_menu.addAction(warp_action)
        
        tools_menu.addSeparator()
        
        save_options_action = QtGui.QAction("Save Options...", self)
        save_options_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
        save_options_action.triggered.connect(self._show_save_options)
        tools_menu.addAction(save_options_action)
        
        merge_action = QtGui.QAction("Merge Slides...", self)
        merge_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView))
        merge_action.triggered.connect(self._merge_slides)
        tools_menu.addAction(merge_action)

        # Help menu
        help_menu = self.menuBar().addMenu("Help")
        
        user_manual_action = QtGui.QAction("User Manual", self)
        user_manual_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        user_manual_action.triggered.connect(self._open_user_manual)
        help_menu.addAction(user_manual_action)
        
        quick_start_action = QtGui.QAction("Quick Start Guide", self)
        quick_start_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMenuButton))
        quick_start_action.triggered.connect(self._open_quick_start)
        help_menu.addAction(quick_start_action)
        
        help_menu.addSeparator()
        
        report_issue_action = QtGui.QAction("Report Issue", self)
        report_issue_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning))
        report_issue_action.triggered.connect(self._report_issue)
        help_menu.addAction(report_issue_action)
        
        help_menu.addSeparator()
        
        perf_stats_action = QtGui.QAction("Performance Statistics", self)
        perf_stats_action.setShortcut("Ctrl+Shift+P")
        perf_stats_action.triggered.connect(self._show_performance_stats)
        help_menu.addAction(perf_stats_action)
        
        help_menu.addSeparator()
        
        about_action = QtGui.QAction("About VALIS Workstation", self)
        about_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation))
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common operations."""
        # File menu shortcuts
        open_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self._open_slide_folder)
        
        run_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+R"), self)
        run_shortcut.activated.connect(self._start_registration)
        
        # View shortcuts
        blink_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+B"), self)
        blink_shortcut.activated.connect(self._blink)
        
        # General shortcuts
        quit_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)
        
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
        slides = self._project_dock.slides()
        if not slides:
            QtWidgets.QMessageBox.warning(self, "VALIS", "No slides to register.")
            return
        
        config = self._properties_dock.config()
        output_dir = self._repo_root / "output" / config.project_name
        
        # Validate before proceeding
        validation = validate_slides(slides, output_dir)
        
        if validation.has_errors():
            error_msg = "Cannot start registration due to the following errors:\n\n" + "\n".join(f"• {e}" for e in validation.errors)
            QtWidgets.QMessageBox.critical(self, "Validation Failed", error_msg)
            logger.error("Pre-registration validation failed: %s", "; ".join(validation.errors))
            return
        
        if validation.has_warnings():
            warning_msg = "The following warnings were detected:\n\n" + "\n".join(f"• {w}" for w in validation.warnings)
            warning_msg += "\n\nDo you want to proceed anyway?"
            
            reply = QtWidgets.QMessageBox.question(
                self, "Validation Warnings",
                warning_msg,
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                logger.info("Registration cancelled due to validation warnings")
                return
        
        # Confirm before starting registration
        if not self._confirm_registration(slides):
            logger.info("Registration cancelled by user")
            return
        
        self._status_bar.showMessage(f"Starting registration of {len(slides)} slides...")
        logger.info("Starting registration with %d slides", len(slides))
        
        self._worker_thread = QtCore.QThread(self)
        self._worker = ValisWorker(config, slides, output_dir)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.started.connect(lambda: self._status_dock.set_progress(0))
        self._worker.started.connect(lambda: self._status_dock.show_cancel_button(True))
        self._worker.progress.connect(self._status_dock.set_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.cancelled.connect(self._on_worker_cancelled)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.cancelled.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._cleanup_worker)
        
        # Connect cancel button
        self._status_dock.connect_cancel(self._request_cancellation)

        self._worker_thread.start()

    def _cleanup_worker(self) -> None:
        self._status_dock.show_cancel_button(False)
        self._worker_thread = None
        self._worker = None

    def _request_cancellation(self) -> None:
        """Handle user request to cancel registration."""
        if not self._worker:
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Cancel Registration",
            "Are you sure you want to cancel the registration?\nPartial results may be lost.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            logger.info("User requested cancellation")
            self._worker.cancel()
            self._status_bar.showMessage("Canceling registration...")

    def _on_worker_cancelled(self) -> None:
        """Handle worker cancellation."""
        logger.info("Registration cancelled")
        self._status_dock.set_progress(0)
        self._status_bar.showMessage("Registration cancelled", 5000)
        QtWidgets.QMessageBox.information(
            self, "VALIS",
            "Registration was cancelled.\nPartial results may have been saved."
        )

    def _confirm_registration(self, slides: list[Path]) -> bool:
        """Show confirmation dialog with *all* settings before starting."""
        config = self._properties_dock.config()

        # Compute total input size
        total_size_bytes = sum(s.stat().st_size for s in slides if s.exists())
        total_size_gb = total_size_bytes / (1024 ** 3)

        # Rough time estimate
        est_minutes = len(slides) * 2
        if config.non_rigid_registration:
            est_minutes *= 1.5
        if config.max_image_size > 4096:
            est_minutes *= 1.5
        if config.micro_registration:
            est_minutes *= 2
        if config.use_masks:
            est_minutes *= 1.2

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirm Registration")
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)

        text = f"""<h3>Ready to Register {len(slides)} Slide{'s' if len(slides) != 1 else ''}</h3>
<table style="margin: 6px 0;">
<tr><td><b>Total size:</b></td><td>{total_size_gb:.2f} GB</td></tr>
<tr><td><b>Estimated time:</b></td><td>~{int(est_minutes)} min</td></tr>
<tr><td><b>Project:</b></td><td>{config.project_name}</td></tr>
</table>
<p><b>Registration settings</b></p>
<table style="margin: 4px 0;">
<tr><td>Rigid registration:</td><td>{'Yes' if config.rigid_registration else 'No'}</td></tr>
<tr><td>Non-rigid registration:</td><td>{'Yes' if config.non_rigid_registration else 'No'}</td></tr>
<tr><td>Max image size:</td><td>{config.max_image_size} px</td></tr>
<tr><td>Feature detector:</td><td>{config.feature_detector}</td></tr>
<tr><td>Rigid transform:</td><td>{config.transformer_type}</td></tr>
<tr><td>Reference slide:</td><td>{config.reference_slide or 'Auto-detect'}</td></tr>
<tr><td>Crop mode:</td><td>{config.crop_mode}</td></tr>
<tr><td>Tissue masks:</td><td>{'Yes' if config.use_masks else 'No'}</td></tr>
<tr><td>Denoise:</td><td>{'Yes' if config.denoise else 'No'}</td></tr>
<tr><td>Slides pre-ordered:</td><td>{'Yes' if config.imgs_ordered else 'No (auto-sort)'}</td></tr>
<tr><td>Micro-registration:</td><td>{'Yes (' + str(config.micro_max_image_size) + ' px)' if config.micro_registration else 'No'}</td></tr>
<tr><td>GPU:</td><td>{'Yes' if config.use_gpu else 'No'}</td></tr>
</table>
<p><b>Output settings</b></p>
<table style="margin: 4px 0;">
<tr><td>Compression:</td><td>{config.compression_level}</td></tr>
<tr><td>Pyramid levels:</td><td>{config.pyramid_levels}</td></tr>
<tr><td>Tile size:</td><td>{config.tile_size} px</td></tr>
<tr><td>JPEG quality:</td><td>{config.image_quality}%</td></tr>
</table>
<p>Proceed?</p>"""

        msg.setText(text)
        msg.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)

        return msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes

    def _on_worker_finished(self, result: dict) -> None:
        logger.info("Registration completed")
        self._status_dock.set_progress(100)
        self._last_result = result
        self._load_registered_layers(result)
        self._status_bar.showMessage("Registration completed successfully", 5000)
        QtWidgets.QMessageBox.information(
            self, "VALIS", "Registration complete."
        )

    def _on_worker_failed(self, message: str) -> None:
        logger.error("Registration failed: %s", message)
        self._status_bar.showMessage("Registration failed", 5000)
        
        # Find log file
        log_file = self._repo_root / "logs" / "valis_workstation.log"
        
        # Show enhanced error dialog
        show_error_dialog(
            self,
            f"Registration failed: {message}",
            exception=None,  # We don't have the exception object here
            log_file=log_file if log_file.exists() else None
        )

    def _blink(self) -> None:
        if not self._napari_available or self._viewer is None:
            QtWidgets.QMessageBox.warning(self, "Blink", "Napari not available.")
            return
        if not self._last_result or not self._last_result.get("registered_dir"):
            QtWidgets.QMessageBox.warning(self, "Blink", "No registered slides available.")
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
            QtWidgets.QMessageBox.warning(self, "Quality Report", "No results available.")
            return
        logger.info("Opening quality report dialog")
        summary_df = self._last_result["summary_df"]
        dialog = QualityReportDialog(summary_df, self)
        dialog.exec()

    def _warp_annotations(self) -> None:
        if not self._last_result or "registrar" not in self._last_result:
            QtWidgets.QMessageBox.warning(self, "Warp", "No registration results available.")
            return
        output_dir = Path(self._last_result["output_dir"])
        dialog = WarpAnnotationsDialog(self._last_result["registrar"], output_dir, self)
        dialog.exec()

    def _load_registered_layers(self, result: dict) -> None:
        if not self._napari_available or self._viewer is None:
            return
        registered_dir = Path(result["registered_dir"])
        for layer in list(self._viewer.layers):
            if layer.name.startswith("Registered:"):
                self._viewer.layers.remove(layer)
        for slide_path in sorted(registered_dir.glob("*.ome.tiff")):
            try:
                layer_result = self._viewer.open(
                    str(slide_path), name=f"Registered: {slide_path.name}"
                )
                if isinstance(layer_result, list):
                    for layer in layer_result:
                        layer.name = f"Registered: {layer.name}"
            except Exception:
                logger.exception("Failed to load registered slide %s", slide_path)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event with proper resource cleanup."""
        logger.info("Closing main window - initiating cleanup")
        
        # Save window state
        self._save_window_state()
        
        # Stop and cleanup worker thread if running
        if self._worker_thread and self._worker_thread.isRunning():
            logger.warning("Worker thread still running - requesting termination")
            
            # Try to cancel the worker first
            if self._worker:
                self._worker.cancel()
            
            # Give it time to finish gracefully
            self._worker_thread.quit()
            if not self._worker_thread.wait(2000):  # Wait max 2 seconds
                logger.error("Worker thread did not terminate gracefully, forcing termination")
                self._worker_thread.terminate()
                self._worker_thread.wait(500)
        
        # Cleanup napari viewer
        if self._viewer is not None:
            try:
                logger.info("Closing napari viewer")
                self._viewer.close()
                self._viewer = None
            except Exception as e:
                logger.exception(f"Failed to close napari viewer: {e}")
        
        # Clear references to help garbage collection
        self._worker = None
        self._worker_thread = None
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

    def _open_user_manual(self) -> None:
        """Open the user manual in default browser."""
        manual_path = self._repo_root / "USER_MANUAL.md"
        if manual_path.exists():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(manual_path)))
            logger.info("Opened user manual")
        else:
            QtWidgets.QMessageBox.information(
                self, "User Manual",
                f"User manual not found at {manual_path}"
            )

    def _open_quick_start(self) -> None:
        """Open the quick start guide in default browser."""
        quick_start_path = self._repo_root / "QUICK_START.md"
        if quick_start_path.exists():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(quick_start_path)))
            logger.info("Opened quick start guide")
        else:
            QtWidgets.QMessageBox.information(
                self, "Quick Start",
                f"Quick start guide not found at {quick_start_path}"
            )

    def _report_issue(self) -> None:
        """Open GitHub issue page."""
        url = "https://github.com/cdgatenbee/valis-wsi/issues/new"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        logger.info("Opened GitHub issues page")

    def _show_about(self) -> None:
        """Show About dialog."""
        about_text = """<h2>VALIS Workstation</h2>
<p><b>Version:</b> 1.0.0</p>
<p><b>Description:</b> Virtual Alignment of pathology Image Series</p>
<p>A GUI application for registering and aligning whole slide images.</p>
<p><b>Based on:</b> VALIS library by Chris Gatenbee</p>
<p><b>License:</b> MIT License</p>
<p><b>GitHub:</b> <a href='https://github.com/cdgatenbee/valis-wsi'>github.com/cdgatenbee/valis-wsi</a></p>
"""
        QtWidgets.QMessageBox.about(self, "About VALIS Workstation", about_text)

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
                logger.info(f"Dropped folder: {path}")
                self._load_slides_from_folder(path)
                break  # Only process first folder
            elif path.is_file():
                # Check if it's a config file
                if path.suffix.lower() == '.json':
                    logger.info(f"Dropped config file: {path}")
                    self._load_config_from_path(path)
                    break
        event.acceptProposedAction()

    def _load_slides_from_folder(self, folder: Path) -> None:
        """Load slides from a folder path."""
        try:
            slides = scan_slide_folder(folder)
            if slides:
                self._project_dock.set_slides(slides)
                self._add_to_recent_folders(str(folder))
                
                # Update reference slide list in properties dock
                slide_names = [s.stem for s in slides]
                self._properties_dock.update_reference_slide_list(slide_names)
                
                # Update slide preview dock with real thumbnails (parallel loading)
                self._slide_preview_dock.clear()
                self._load_thumbnails_parallel(slides)
                
                logger.info("Loaded %d slides from %s", len(slides), folder.name)
                self._status_bar.showMessage(f"Loaded {len(slides)} slides from {folder.name}")
            else:
                QtWidgets.QMessageBox.warning(
                    self, "No Slides Found",
                    f"No supported slide images found in {folder.name}"
                )
        except Exception as e:
            logger.exception("Failed to load slides from %s", folder)
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"Failed to load slides from {folder.name}:\n{str(e)}"
            )

    def _load_thumbnails_parallel(self, slides: list[Path]) -> None:
        """Load thumbnails in parallel using thread pool.
        
        Parameters
        ----------
        slides : list[Path]
            List of slide file paths to generate thumbnails for
        """
        import concurrent.futures
        from valis_workstation.services.thumbnail_generator import generate_thumbnail
        
        total_slides = len(slides)
        completed = 0
        
        # Update status bar
        self._status_bar.showMessage(f"Generating thumbnails: 0/{total_slides}")
        
        def generate_and_update(slide_path: Path) -> tuple[str, QtGui.QPixmap | None, dict]:
            """Generate thumbnail and return results."""
            try:
                thumbnail, metadata = generate_thumbnail(slide_path, max_size=512)
                return slide_path.stem, thumbnail, metadata
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail for {slide_path.name}: {e}")
                return slide_path.stem, None, {"file_path": str(slide_path)}
        
        # Use ThreadPoolExecutor with limited workers to avoid overwhelming disk I/O
        # 4 workers is a good balance for I/O bound operations
        max_workers = min(4, total_slides)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_slide = {
                executor.submit(generate_and_update, slide): slide 
                for slide in slides
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_slide):
                slide_name, thumbnail, metadata = future.result()
                
                # Add to preview dock
                self._slide_preview_dock.add_slide(slide_name, thumbnail, metadata)
                
                # Update progress
                completed += 1
                self._status_bar.showMessage(f"Generating thumbnails: {completed}/{total_slides}")
                
                # Process events to keep UI responsive
                QtWidgets.QApplication.processEvents()
        
        logger.info(f"Generated {completed}/{total_slides} thumbnails")

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
        logger.debug(f"Added {folder_path} to recent folders")

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
                action = self._recent_menu.addAction(path.name)
                action.setToolTip(folder_path)
                action.triggered.connect(
                    lambda checked=False, p=path: self._load_slides_from_folder(p)
                )

    def _save_configuration(self) -> None:
        """Save current configuration to JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Configuration",
            str(self._repo_root / "configs"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            import dataclasses, json
            config = self._properties_dock.config()
            config_dict = dataclasses.asdict(config)
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info("Saved configuration to %s", file_path)
            self._status_bar.showMessage(f"Configuration saved to {Path(file_path).name}", 3000)
        except Exception as e:
            logger.exception("Failed to save configuration")
            QtWidgets.QMessageBox.critical(
                self, "Save Error",
                f"Failed to save configuration:\n{e}"
            )

    def _load_configuration(self) -> None:
        """Load configuration from JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Configuration",
            str(self._repo_root / "configs"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        self._load_config_from_path(Path(file_path))

    def _load_config_from_path(self, file_path: Path) -> None:
        """Load configuration from a JSON file and populate the dock."""
        try:
            import json
            with open(file_path, 'r') as f:
                config_dict = json.load(f)

            # Build a Config from the dict, falling back to defaults for
            # any keys that are missing (e.g. older config files).
            cfg = Config(**{k: v for k, v in config_dict.items()
                            if k in Config.__dataclass_fields__})

            self._properties_dock.set_config(cfg)

            logger.info("Loaded configuration from %s", file_path)
            self._status_bar.showMessage(
                f"Configuration loaded from {file_path.name}", 3000
            )
        except Exception as e:
            logger.exception("Failed to load configuration")
            QtWidgets.QMessageBox.critical(
                self, "Load Error",
                f"Failed to load configuration:\n{e}"
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
                self, "Merge Slides",
                "No registered slides available. Please run registration first."
            )
            return
        
        # Get list of slide names from the registrar
        registrar = self._last_result["registrar"]
        slide_names = [slide.name for slide in registrar.slide_dict.values()]
        
        if len(slide_names) < 2:
            QtWidgets.QMessageBox.warning(
                self, "Merge Slides",
                "Need at least 2 registered slides to merge."
            )
            return
        
        dialog = MergeSlidesDialog(slide_names, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            merge_config = dialog.get_merge_config()
            logger.info(f"Merge configuration: {merge_config}")
            
            if not merge_config["channels"]:
                QtWidgets.QMessageBox.warning(
                    self, "Merge Slides",
                    "No channels selected for merging."
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
                f"Merging {len(merge_config['channels'])} channels...",
                0
            )
            
            merge_thread = QtCore.QThread(self)
            
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
            
            merge_worker = _MergeWorker(registrar, merge_config, output_dir, save_config)
            merge_worker.moveToThread(merge_thread)
            
            def on_merge_success(result_path):
                logger.info(f"Merge completed: {result_path}")
                self._status_bar.showMessage(f"Slides merged successfully", 5000)
                QtWidgets.QMessageBox.information(
                    self, "Merge Complete",
                    f"Successfully merged {len(merge_config['channels'])} channels.\n\n"
                    f"Output: {result_path}"
                )
                merge_thread.quit()
            
            def on_merge_error(msg):
                logger.error(f"Merge failed: {msg}")
                self._status_bar.showMessage("Merge failed", 5000)
                QtWidgets.QMessageBox.critical(
                    self, "Merge Failed",
                    f"Failed to merge slides:\n{msg}"
                )
                merge_thread.quit()
            
            merge_worker.finished.connect(on_merge_success)
            merge_worker.failed.connect(on_merge_error)
            merge_thread.started.connect(merge_worker.run)
            merge_thread.start()
    
    def _show_performance_stats(self) -> None:
        """Show the performance statistics dialog."""
        from valis_workstation.ui.dialogs.performance_stats_dialog import PerformanceStatsDialog
        
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
            "Some preference changes require restarting the application to take effect."
        )

