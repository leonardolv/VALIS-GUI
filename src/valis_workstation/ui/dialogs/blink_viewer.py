from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets


class BlinkViewerDialog(QtWidgets.QDialog):
    def __init__(
        self,
        viewer,
        slide_paths: list[Path],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Blink Viewer")
        self.resize(360, 200)
        self._viewer = viewer
        self._slide_paths = slide_paths
        self._layer_a = None
        self._layer_b = None
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(600)
        self._timer.timeout.connect(self._toggle_layers)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._slide_a = QtWidgets.QComboBox()
        self._slide_b = QtWidgets.QComboBox()
        for slide in slide_paths:
            self._slide_a.addItem(slide.name, slide)
            self._slide_b.addItem(slide.name, slide)

        self._opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._opacity.setRange(0, 100)
        self._opacity.setValue(50)
        self._opacity.valueChanged.connect(self._apply_opacity)

        self._blink_toggle = QtWidgets.QPushButton("Start Blink")
        self._blink_toggle.setCheckable(True)
        self._blink_toggle.toggled.connect(self._toggle_blink)

        self._slide_a.currentIndexChanged.connect(self._reload_layers)
        self._slide_b.currentIndexChanged.connect(self._reload_layers)

        form.addRow("Slide A", self._slide_a)
        form.addRow("Slide B", self._slide_b)
        form.addRow("Blend", self._opacity)
        layout.addLayout(form)
        layout.addWidget(self._blink_toggle)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._reload_layers()

    def _reload_layers(self) -> None:
        if self._layer_a is not None:
            self._viewer.layers.remove(self._layer_a)
        if self._layer_b is not None:
            self._viewer.layers.remove(self._layer_b)

        slide_a = self._slide_a.currentData()
        slide_b = self._slide_b.currentData()
        if not slide_a or not slide_b:
            return

        self._layer_a = self._normalize_layer(
            self._viewer.open(str(slide_a), name=f"Blink A: {slide_a.name}")
        )
        self._layer_b = self._normalize_layer(
            self._viewer.open(str(slide_b), name=f"Blink B: {slide_b.name}")
        )
        self._apply_opacity()
        self._set_layer_visibility(True)

    @staticmethod
    def _normalize_layer(layer_result):
        if isinstance(layer_result, list):
            return layer_result[0] if layer_result else None
        return layer_result

    def _apply_opacity(self) -> None:
        if self._layer_a is None or self._layer_b is None:
            return
        value = self._opacity.value() / 100
        self._layer_a.opacity = 1 - value
        self._layer_b.opacity = value

    def _toggle_blink(self, enabled: bool) -> None:
        if enabled:
            self._blink_toggle.setText("Stop Blink")
            self._timer.start()
        else:
            self._blink_toggle.setText("Start Blink")
            self._timer.stop()
            self._set_layer_visibility(True)

    def _toggle_layers(self) -> None:
        if self._layer_a is None or self._layer_b is None:
            return
        showing_a = self._layer_a.visible
        self._set_layer_visibility(not showing_a)

    def _set_layer_visibility(self, show_a: bool) -> None:
        if self._layer_a is None or self._layer_b is None:
            return
        self._layer_a.visible = show_a
        self._layer_b.visible = not show_a

    def closeEvent(self, event) -> None:
        self._timer.stop()
        super().closeEvent(event)
