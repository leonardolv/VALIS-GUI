from __future__ import annotations

import json
from pathlib import Path

from PySide6 import QtWidgets


class WarpAnnotationsDialog(QtWidgets.QDialog):
    def __init__(
        self,
        registrar,
        output_dir: Path,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Warp Annotations")
        self.resize(480, 220)
        self._registrar = registrar
        self._output_dir = Path(output_dir)
        self._use_non_rigid = registrar.non_rigid_registrar_cls is not None

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._annotation_path = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_annotation)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self._annotation_path)
        path_layout.addWidget(browse_btn)

        self._source_slide = QtWidgets.QComboBox()
        for slide_path in registrar.get_sorted_img_f_list():
            slide_obj = registrar.get_slide(slide_path)
            self._source_slide.addItem(slide_obj.name, slide_path)

        self._output_dir_edit = QtWidgets.QLineEdit(str(self._output_dir / "warped_annotations"))
        out_btn = QtWidgets.QPushButton("Browse")
        out_btn.clicked.connect(self._browse_output)
        out_layout = QtWidgets.QHBoxLayout()
        out_layout.addWidget(self._output_dir_edit)
        out_layout.addWidget(out_btn)

        form.addRow("Annotation file", path_layout)
        form.addRow("Source slide", self._source_slide)
        form.addRow("Output directory", out_layout)

        layout.addLayout(form)

        self._status = QtWidgets.QLabel()
        layout.addWidget(self._status)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._run_warp)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _browse_annotation(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Annotation File", filter="GeoJSON (*.geojson)"
        )
        if path:
            self._annotation_path.setText(path)

    def _browse_output(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir_edit.setText(folder)

    def _run_warp(self) -> None:
        annotation_path = Path(self._annotation_path.text()).expanduser()
        if not annotation_path.exists():
            QtWidgets.QMessageBox.warning(self, "Warp", "Annotation file not found.")
            return

        output_dir = Path(self._output_dir_edit.text()).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        source_slide_path = self._source_slide.currentData()
        if not source_slide_path:
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
            output_path = output_dir / f"{source_slide.name}_to_{target_slide.name}.geojson"
            output_path.write_text(json.dumps(warped_geojson))

        self._status.setText(f"Warped annotations saved to {output_dir}")
        self.accept()
