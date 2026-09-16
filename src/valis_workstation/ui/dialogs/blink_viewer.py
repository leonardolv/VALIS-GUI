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
        self._reduced_motion = QtCore.QSettings("VALIS", "Workstation").value(
            "ui/reduced_motion", False, type=bool
        )
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(600)
        self._timer.timeout.connect(self._toggle_layers)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._slide_a = QtWidgets.QComboBox()
        self._slide_a.setToolTip("Select a registered slide for this channel")
        self._slide_b = QtWidgets.QComboBox()
        self._slide_b.setToolTip("Select a registered slide for this channel")
        for slide in slide_paths:
            self._slide_a.addItem(slide.name, slide)
            self._slide_b.addItem(slide.name, slide)

        self._opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._opacity.setRange(0, 100)
        self._opacity.setValue(50)
        self._opacity.setToolTip("0% = Slide A only · 100% = Slide B only · 50% = equal blend")
        self._opacity.valueChanged.connect(self._apply_opacity)

        self._mode = QtWidgets.QComboBox()
        self._mode.addItems(["Blink", "Side-by-side", "Swipe"])
        self._mode.setToolTip("Blink: auto-toggle · Blend: manual crossfade · Swipe: horizontal split")
        self._mode.currentTextChanged.connect(self._on_mode_changed)

        self._blink_toggle = QtWidgets.QPushButton("Start Blink")
        self._blink_toggle.setCheckable(True)
        self._blink_toggle.toggled.connect(self._toggle_blink)

        if self._reduced_motion:
            self._disable_blink_mode_for_reduced_motion()

        self._slide_a.currentIndexChanged.connect(self._reload_layers)
        self._slide_b.currentIndexChanged.connect(self._reload_layers)

        form.addRow("Slide A", self._slide_a)
        form.addRow("Slide B", self._slide_b)
        form.addRow("Mode", self._mode)
        form.addRow("Blend", self._opacity)
        layout.addLayout(form)
        layout.addWidget(self._blink_toggle)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._reload_layers()

    def _disable_blink_mode_for_reduced_motion(self) -> None:
        """Blink mode auto-toggles layer visibility on a timer - exactly
        the strobing motion ``ui/reduced_motion`` exists to suppress. The
        item is disabled rather than removed, so re-enabling the
        preference later still finds the option where it was;
        Side-by-side and Swipe (both static) remain fully available."""
        blink_index = self._mode.findText("Blink")
        if blink_index != -1:
            blink_item = self._mode.model().item(blink_index)
            if blink_item is not None:
                blink_item.setEnabled(False)
            if self._mode.currentIndex() == blink_index:
                self._mode.setCurrentText("Side-by-side")
        self._mode.setToolTip(
            "Blink is disabled while Reduce Motion is enabled in "
            "Preferences. Side-by-side: static overlay · Swipe: "
            "horizontal split"
        )
        self._blink_toggle.setEnabled(False)
        self._blink_toggle.setToolTip(
            "Disabled while Reduce Motion is enabled in Preferences"
        )

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
        self._on_mode_changed(self._mode.currentText())

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

    def _on_mode_changed(self, mode: str) -> None:
        if self._layer_a is None or self._layer_b is None:
            return
        if mode != "Blink":
            self._blink_toggle.setChecked(False)
            self._timer.stop()
            self._blink_toggle.setEnabled(False)
        else:
            self._blink_toggle.setEnabled(True)

        if mode == "Side-by-side":
            # Best-effort side-by-side fallback in layer stack: show both fully.
            self._layer_a.visible = True
            self._layer_b.visible = True
            self._layer_a.opacity = 1.0
            self._layer_b.opacity = 1.0
        elif mode == "Swipe":
            # Swipe approximation: blend controlled by slider.
            self._layer_a.visible = True
            self._layer_b.visible = True
            self._apply_opacity()
        else:
            self._apply_opacity()
            self._set_layer_visibility(True)

    def _toggle_blink(self, enabled: bool) -> None:
        if enabled and self._reduced_motion:
            # Defense in depth: the button being disabled stops normal
            # mouse/keyboard interaction, but `setChecked` can still be
            # called programmatically - the strobing timer must never
            # start while Reduce Motion is on, regardless of how the
            # toggle was flipped.
            self._blink_toggle.setChecked(False)
            return
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
