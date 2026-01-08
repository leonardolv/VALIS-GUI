from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from valis_workstation.models.config import Config

SIMPLE_ELASTIX_BANNER = (
    "SimpleElastix not found. Only Rigid Registration is available. "
    "Please install SimpleElastix for full functionality."
)


class PropertiesDock(QtWidgets.QDockWidget):
    def __init__(self, simple_elastix_available: bool, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Properties", parent)
        self._simple_elastix_available = simple_elastix_available

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        self._banner = QtWidgets.QLabel()
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet("color: #ffcc66; font-weight: bold;")
        layout.addWidget(self._banner)

        form = QtWidgets.QFormLayout()
        self._project_name = QtWidgets.QLineEdit("New Project")
        self._rigid = QtWidgets.QCheckBox()
        self._rigid.setChecked(True)
        self._non_rigid = QtWidgets.QCheckBox()
        self._non_rigid.setChecked(True)
        self._max_size = QtWidgets.QSpinBox()
        self._max_size.setRange(256, 16384)
        self._max_size.setValue(2048)
        self._match_threshold = QtWidgets.QDoubleSpinBox()
        self._match_threshold.setRange(0.0, 1.0)
        self._match_threshold.setSingleStep(0.05)
        self._match_threshold.setValue(0.35)
        self._use_gpu = QtWidgets.QCheckBox()

        form.addRow("Project name", self._project_name)
        form.addRow("Rigid registration", self._rigid)
        form.addRow("Non-rigid registration", self._non_rigid)
        form.addRow("Max image size", self._max_size)
        form.addRow("Match threshold", self._match_threshold)
        form.addRow("Use GPU", self._use_gpu)

        layout.addLayout(form)
        layout.addStretch(1)
        self.setWidget(container)

        self._apply_simple_elastix_state()

    def _apply_simple_elastix_state(self) -> None:
        if not self._simple_elastix_available:
            self._banner.setText(SIMPLE_ELASTIX_BANNER)
            self._non_rigid.setChecked(False)
            self._non_rigid.setEnabled(False)
        else:
            self._banner.setText("")

    def config(self) -> Config:
        return Config(
            project_name=self._project_name.text().strip() or "New Project",
            rigid_registration=self._rigid.isChecked(),
            non_rigid_registration=self._non_rigid.isChecked(),
            max_image_size=int(self._max_size.value()),
            match_threshold=float(self._match_threshold.value()),
            use_gpu=self._use_gpu.isChecked(),
        )
