from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6 import QtCore, QtWidgets


class WarpAnnotationsDialog(QtWidgets.QDialog):
    def __init__(
        self,
        registrar,
        output_dir: Path,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Warp Annotations")
        self.resize(500, 240)
        self.setModal(True)
        self._registrar = registrar
        self._output_dir = Path(output_dir)
        self._use_non_rigid = getattr(registrar, "non_rigid_registrar_cls", None) is not None

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._annotation_path = QtWidgets.QLineEdit()
        self._annotation_path.setObjectName("annotation_path")
        self._annotation_path.setAccessibleName("Annotation file path")
        self._annotation_path.setPlaceholderText("Path to source .geojson annotation file...")
        self._annotation_path.setToolTip("GeoJSON file containing regions of interest from the source slide")

        self._browse_annotation_btn = QtWidgets.QPushButton("Browse")
        self._browse_annotation_btn.setObjectName("browse_annotation_btn")
        self._browse_annotation_btn.setAccessibleName("Browse annotation file")
        self._browse_annotation_btn.setToolTip("Browse filesystem for source GeoJSON annotation file")
        self._browse_annotation_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._browse_annotation_btn.clicked.connect(self._browse_annotation)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self._annotation_path)
        path_layout.addWidget(self._browse_annotation_btn)

        self._source_slide = QtWidgets.QComboBox()
        self._source_slide.setObjectName("source_slide")
        self._source_slide.setAccessibleName("Source slide selection")
        self._source_slide.setToolTip("The slide the annotations were drawn on")
        self._source_slide.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        if hasattr(registrar, "get_sorted_img_f_list"):
            for slide_path in registrar.get_sorted_img_f_list():
                slide_obj = registrar.get_slide(slide_path)
                self._source_slide.addItem(slide_obj.name, slide_path)

        self._output_dir_edit = QtWidgets.QLineEdit(
            str(self._output_dir / "warped_annotations")
        )
        self._output_dir_edit.setObjectName("output_dir_edit")
        self._output_dir_edit.setAccessibleName("Warped annotations output directory")
        self._output_dir_edit.setPlaceholderText("Directory where warped GeoJSON files will be saved...")
        self._output_dir_edit.setToolTip("Directory where warped GeoJSON files will be saved (one per target slide)")

        self._browse_output_btn = QtWidgets.QPushButton("Browse")
        self._browse_output_btn.setObjectName("browse_output_btn")
        self._browse_output_btn.setAccessibleName("Browse output directory")
        self._browse_output_btn.setToolTip("Browse filesystem for output folder")
        self._browse_output_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._browse_output_btn.clicked.connect(self._browse_output)

        out_layout = QtWidgets.QHBoxLayout()
        out_layout.addWidget(self._output_dir_edit)
        out_layout.addWidget(self._browse_output_btn)

        form.addRow("Annotation file", path_layout)
        form.addRow("Source slide", self._source_slide)
        form.addRow("Output directory", out_layout)

        layout.addLayout(form)

        self._status = QtWidgets.QLabel()
        self._status.setObjectName("status_label")
        self._status.setAccessibleName("Warp status message")
        layout.addWidget(self._status)

        self._button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = self._button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if self._ok_btn:
            self._ok_btn.setObjectName("ok_btn")
            self._ok_btn.setAccessibleName("Warp annotations")
            self._ok_btn.setToolTip("Transform and save warped annotations to target slides")
            self._ok_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._cancel_btn = self._button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        if self._cancel_btn:
            self._cancel_btn.setObjectName("cancel_btn")
            self._cancel_btn.setAccessibleName("Cancel")
            self._cancel_btn.setToolTip("Close dialog without saving warped annotations")
            self._cancel_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._button_box.accepted.connect(self._run_warp)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    def _browse_annotation(self) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        last_dir = settings.value("ui/last_warp_annotation_dir", str(Path.home()))

        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Annotation File", last_dir, filter="GeoJSON (*.geojson)"
        )
        if path:
            settings.setValue("ui/last_warp_annotation_dir", str(Path(path).parent))
            self._annotation_path.setText(path)

    def _browse_output(self) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        last_dir = settings.value("ui/last_warp_output_dir", str(Path.home()))

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Folder", last_dir
        )
        if folder:
            settings.setValue("ui/last_warp_output_dir", folder)
            self._output_dir_edit.setText(folder)

    def _run_warp(self) -> None:
        raw_path = self._annotation_path.text().strip()
        annotation_path = Path(raw_path).expanduser() if raw_path else Path("")
        if not raw_path or not annotation_path.exists():
            self._status.setText("Annotation file not found.")
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen" and not os.environ.get("PYTEST_CURRENT_TEST"):
                QtWidgets.QMessageBox.warning(self, "Warp", "Annotation file not found.")
            return

        output_dir = Path(self._output_dir_edit.text()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._status.setText(f"Failed to create output directory: {e}")
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen" and not os.environ.get("PYTEST_CURRENT_TEST"):
                QtWidgets.QMessageBox.warning(self, "Warp", f"Failed to create output directory: {e}")
            return

        source_slide_path = self._source_slide.currentData()
        if not source_slide_path:
            self._status.setText("Select a source slide.")
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen" and not os.environ.get("PYTEST_CURRENT_TEST"):
                QtWidgets.QMessageBox.warning(self, "Warp", "Select a source slide.")
            return

        source_slide = self._registrar.get_slide(source_slide_path)

        for target_path in self._registrar.get_sorted_img_f_list():
            target_slide = self._registrar.get_slide(target_path)
            warped_geojson = source_slide.warp_geojson_from_to(
                str(annotation_path),
                to_slide_obj=target_slide,
                src_slide_level=0,
                src_pt_level=0,
                non_rigid=self._use_non_rigid,
                crop=True,
            )
            output_path = (
                output_dir / f"{source_slide.name}_to_{target_slide.name}.geojson"
            )
            output_path.write_text(json.dumps(warped_geojson))

        self._status.setText(f"Warped annotations saved to {output_dir}")
        self.accept()
