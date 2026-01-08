from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from valis_workstation.models.config import Config
from valis_workstation.services.error_metrics import select_metric_column
from valis_workstation.services.slide_scan import scan_slide_folder
from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog
from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog
from valis_workstation.ui.dialogs.quality_report import QualityReportDialog
from valis_workstation.ui.dialogs.warp_annotations import WarpAnnotationsDialog
from valis_workstation.ui.layer_controls_dock import LayerControlsDock
from valis_workstation.ui.project_dock import ProjectDock
from valis_workstation.ui.properties_dock import PropertiesDock
from valis_workstation.ui.status_dock import StatusDock
from valis_workstation.utils.qt_logging import QtLogEmitter
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
        self._layer_controls: LayerControlsDock | None = None

        self.setWindowTitle("VALIS Workstation")
        self.resize(1400, 900)

        self._project_dock = ProjectDock(self)
        self._properties_dock = PropertiesDock(simple_elastix_available, self)
        self._status_dock = StatusDock(log_emitter, self)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._project_dock)
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self._properties_dock
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self._status_dock
        )

        self.setCentralWidget(self._build_central_widget())
        self._build_actions()

    def _build_central_widget(self) -> QtWidgets.QWidget:
        napari_spec = importlib.util.find_spec("napari")
        if napari_spec is None:
            return self._napari_unavailable_widget()

        napari_module = importlib.import_module("napari")
        try:
            self._viewer = napari_module.Viewer(show=False)
            self._napari_available = True
        except Exception:
            logger.exception("Failed to start napari viewer")
            return self._napari_unavailable_widget()

        self._layer_controls = LayerControlsDock(self._viewer, self)
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self._layer_controls
        )

        return self._viewer.window._qt_window

    def _napari_unavailable_widget(self) -> QtWidgets.QWidget:
        label = QtWidgets.QLabel("Napari not available")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return label

    def _build_actions(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        open_action = QtWidgets.QAction("Open Slide Folder", self)
        open_action.triggered.connect(self._open_slide_folder)
        file_menu.addAction(open_action)

        run_action = QtWidgets.QAction("Run Registration", self)
        run_action.triggered.connect(self._start_registration)
        file_menu.addAction(run_action)

        tools_menu = self.menuBar().addMenu("Tools")
        blink_action = QtWidgets.QAction("Blink", self)
        blink_action.triggered.connect(self._blink)
        tools_menu.addAction(blink_action)

        plot_action = QtWidgets.QAction("Analysis Plot", self)
        plot_action.triggered.connect(self._show_analysis_plot)
        tools_menu.addAction(plot_action)

        warp_action = QtWidgets.QAction("Warp Annotations", self)
        warp_action.triggered.connect(self._warp_annotations)
        tools_menu.addAction(warp_action)

        report_action = QtWidgets.QAction("Quality Report", self)
        report_action.triggered.connect(self._show_quality_report)
        tools_menu.addAction(report_action)

    def _open_slide_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Slide Folder")
        if not folder:
            return
        slides = scan_slide_folder(Path(folder))
        self._project_dock.set_slides(slides)
        logger.info("Loaded %d slides", len(slides))

    def _start_registration(self) -> None:
        slides = self._project_dock.slides()
        if not slides:
            QtWidgets.QMessageBox.warning(self, "VALIS", "No slides to register.")
            return
        config = self._properties_dock.config()
        output_dir = self._repo_root / "output" / config.project_name

        self._worker_thread = QtCore.QThread(self)
        self._worker = ValisWorker(config, slides, output_dir)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.started.connect(lambda: self._status_dock.set_progress(0))
        self._worker.progress.connect(self._status_dock.set_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._cleanup_worker)

        self._worker_thread.start()

    def _cleanup_worker(self) -> None:
        self._worker_thread = None
        self._worker = None

    def _on_worker_finished(self, result: dict) -> None:
        logger.info("Registration completed")
        self._status_dock.set_progress(100)
        self._last_result = result
        self._load_registered_layers(result)
        self._add_quality_overlays(result)
        QtWidgets.QMessageBox.information(
            self, "VALIS", "Registration complete."
        )

    def _on_worker_failed(self, message: str) -> None:
        logger.error("Registration failed: %s", message)
        QtWidgets.QMessageBox.critical(
            self, "VALIS", f"Registration failed: {message}"
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
        summary_df = self._last_result["summary_df"]
        dialog = AnalysisPlotDialog(summary_df, self)
        dialog.exec()

    def _show_quality_report(self) -> None:
        if not self._last_result or "summary_df" not in self._last_result:
            QtWidgets.QMessageBox.warning(self, "Quality", "No results available.")
            return
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

        if self._layer_controls is not None:
            self._layer_controls.refresh()

    def _add_quality_overlays(self, result: dict) -> None:
        if not self._napari_available or self._viewer is None:
            return
        summary_df = result.get("summary_df")
        if summary_df is None:
            return

        metric_column = select_metric_column(summary_df)
        if metric_column is None:
            return

        metric_by_slide = (
            summary_df.groupby("from")[metric_column].mean().to_dict()
        )
        values = list(metric_by_slide.values())
        if not values:
            return
        min_val, max_val = min(values), max(values)
        spread = max(max_val - min_val, 1e-6)

        for layer in list(self._viewer.layers):
            if layer.name.startswith("Quality Heatmap"):
                self._viewer.layers.remove(layer)
        if "Quality Markers" in self._viewer.layers:
            self._viewer.layers.remove(self._viewer.layers["Quality Markers"])

        marker_layer = self._viewer.add_shapes(
            name="Quality Markers",
            shape_type="rectangle",
            edge_width=4,
            face_color="transparent",
        )

        for layer in list(self._viewer.layers):
            if not layer.name.startswith("Registered:"):
                continue
            slide_name = layer.name.replace("Registered:", "").strip()
            metric_value = metric_by_slide.get(slide_name, min_val)
            normalized = (metric_value - min_val) / spread
            color = (1.0, 1.0 - normalized, 0.0, 0.9)

            extent = layer.extent.data
            top_left = extent[0]
            bottom_right = extent[1]
            rectangle = [
                [top_left[0], top_left[1]],
                [top_left[0], bottom_right[1]],
                [bottom_right[0], bottom_right[1]],
                [bottom_right[0], top_left[1]],
            ]
            marker_layer.add(rectangle, edge_color=color)

            heatmap = self._build_heatmap_layer(layer, normalized)
            if heatmap is not None:
                self._viewer.add_image(**heatmap)

    @staticmethod
    def _build_heatmap_layer(layer, normalized_value: float) -> dict | None:
        try:
            import numpy as np
        except Exception:
            return None
        extent = layer.extent.data
        top_left = extent[0]
        bottom_right = extent[1]
        height = max(int(bottom_right[0] - top_left[0]), 1)
        width = max(int(bottom_right[1] - top_left[1]), 1)

        base = np.full((64, 64), normalized_value, dtype="float32")
        scale_y = height / base.shape[0]
        scale_x = width / base.shape[1]
        return {
            "data": base,
            "name": f"Quality Heatmap: {layer.name}",
            "colormap": "magma",
            "opacity": 0.35,
            "blending": "additive",
            "translate": (top_left[0], top_left[1]),
            "scale": (scale_y, scale_x),
        }

    def closeEvent(self, event) -> None:
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(2000)
        if self._viewer is not None:
            self._viewer.close()
        super().closeEvent(event)
