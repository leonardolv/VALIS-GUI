"""Napari layer blink viewer for visual verification of registration quality."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6 import QtCore, QtWidgets


class BlinkViewerDialog(QtWidgets.QDialog):
    """Small floating control window to blink / crossfade registered slides in napari."""

    def __init__(
        self,
        viewer,
        slide_paths: Sequence[Path],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("blinkViewerDialog")
        self.setAccessibleName("Blink Viewer Dialog")
        self.setWindowTitle("Blink Viewer")
        self.resize(380, 240)
        self._viewer = viewer
        self._slide_paths = slide_paths
        self._layer_a = None
        self._layer_b = None

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(600)
        self._timer.timeout.connect(self._toggle_layers)
        # QDialog.reject()/accept() - what the "Close" standard button and
        # the Escape key both call - do NOT invoke closeEvent (only a real
        # close()/window-X-button does), so stopping the timer solely from
        # closeEvent leaves it running forever once this dialog (parented
        # to MainWindow) is merely hidden rather than destroyed. `finished`
        # fires on every exit path, so hook that as well.
        self.finished.connect(self._stop_blink_timer)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._slide_a = QtWidgets.QComboBox()
        self._slide_a.setObjectName("blinkSlideACombo")
        self._slide_a.setAccessibleName("Slide A Selection")
        self._slide_a.setToolTip("Select registered slide A for comparison")
        self._slide_a.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._slide_b = QtWidgets.QComboBox()
        self._slide_b.setObjectName("blinkSlideBCombo")
        self._slide_b.setAccessibleName("Slide B Selection")
        self._slide_b.setToolTip("Select registered slide B for comparison")
        self._slide_b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        for slide in slide_paths:
            self._slide_a.addItem(slide.name, slide)
            self._slide_b.addItem(slide.name, slide)

        # Comparing a slide with itself shows nothing; default B to the next slide.
        if len(slide_paths) > 1:
            self._slide_b.setCurrentIndex(1)

        self._mode = QtWidgets.QComboBox()
        self._mode.setObjectName("blinkModeCombo")
        self._mode.setAccessibleName("Display Mode Selection")
        self._mode.addItems(["Blink", "Side-by-side", "Swipe"])
        self._mode.setToolTip("Display mode: Blink (auto-toggle), Side-by-side, or Swipe")
        self._mode.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._mode.currentTextChanged.connect(self._on_mode_changed)

        self._interval_spin = QtWidgets.QSpinBox()
        self._interval_spin.setObjectName("blinkIntervalSpin")
        self._interval_spin.setAccessibleName("Blink Interval Milliseconds")
        self._interval_spin.setRange(100, 3000)
        self._interval_spin.setSingleStep(50)
        self._interval_spin.setValue(600)
        self._interval_spin.setSuffix(" ms")
        self._interval_spin.setToolTip("Interval between alternating slide frames in auto-blink mode (ms)")
        self._interval_spin.valueChanged.connect(self._on_interval_changed)

        self._opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._opacity.setObjectName("blinkOpacitySlider")
        self._opacity.setAccessibleName("Blend Opacity Slider")
        self._opacity.setRange(0, 100)
        self._opacity.setValue(50)
        self._opacity.setToolTip(
            "Blend ratio: 0% = Slide A only - 50% = equal blend - 100% = Slide B only. "
            "Not used in Side-by-side mode."
        )
        self._opacity.valueChanged.connect(self._apply_opacity)

        self._blink_toggle = QtWidgets.QPushButton("Start Blink")
        self._blink_toggle.setObjectName("blinkToggleBtn")
        self._blink_toggle.setAccessibleName("Toggle Auto Blink")
        self._blink_toggle.setToolTip("Start or stop automatic alternating blink between Slide A and Slide B")
        self._blink_toggle.setCheckable(True)
        self._blink_toggle.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._blink_toggle.toggled.connect(self._toggle_blink)

        self._slide_a.currentIndexChanged.connect(self._reload_layers)
        self._slide_b.currentIndexChanged.connect(self._reload_layers)

        form.addRow("Slide A", self._slide_a)
        form.addRow("Slide B", self._slide_b)
        form.addRow("Mode", self._mode)
        form.addRow("Interval", self._interval_spin)
        form.addRow("Blend", self._opacity)
        layout.addLayout(form)
        layout.addWidget(self._blink_toggle)

        self._button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        self._button_box.setObjectName("blinkButtonBox")
        self._button_box.setAccessibleName("Blink Viewer Actions")
        self._close_btn = self._button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        if self._close_btn:
            self._close_btn.setObjectName("blinkCloseBtn")
            self._close_btn.setAccessibleName("Close Blink Viewer")
            self._close_btn.setToolTip("Close the blink viewer dialog")
            self._close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

        self._reload_layers()

    def _on_interval_changed(self, value: int) -> None:
        self._timer.setInterval(value)

    def _reload_layers(self) -> None:
        if self._viewer is None:
            return
        if self._layer_a is not None and hasattr(self._viewer, "layers"):
            try:
                self._viewer.layers.remove(self._layer_a)
            except (ValueError, KeyError, AttributeError):
                pass
        if self._layer_b is not None and hasattr(self._viewer, "layers"):
            try:
                self._viewer.layers.remove(self._layer_b)
            except (ValueError, KeyError, AttributeError):
                pass

        slide_a = self._slide_a.currentData()
        slide_b = self._slide_b.currentData()
        if not slide_a or not slide_b:
            return

        try:
            self._layer_a = self._normalize_layer(
                self._viewer.open(str(slide_a), name=f"Blink A: {slide_a.name}")
            )
            self._layer_b = self._normalize_layer(
                self._viewer.open(str(slide_b), name=f"Blink B: {slide_b.name}")
            )
        except Exception:
            return

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
        if self._mode.currentText() == "Side-by-side":
            # Both layers must stay fully opaque; the slider does not apply.
            return
        value = self._opacity.value() / 100
        try:
            self._layer_a.opacity = 1 - value
            self._layer_b.opacity = value
        except AttributeError:
            pass

    def _on_mode_changed(self, mode: str) -> None:
        self._opacity.setEnabled(mode != "Side-by-side")
        if self._layer_a is None or self._layer_b is None:
            return
        if mode != "Blink":
            self._blink_toggle.setChecked(False)
            self._timer.stop()
            self._blink_toggle.setEnabled(False)
            self._interval_spin.setEnabled(False)
        else:
            self._blink_toggle.setEnabled(True)
            self._interval_spin.setEnabled(True)

        if mode == "Side-by-side":
            # Best-effort side-by-side fallback in layer stack: show both fully.
            try:
                self._layer_a.visible = True
                self._layer_b.visible = True
                self._layer_a.opacity = 1.0
                self._layer_b.opacity = 1.0
            except AttributeError:
                pass
        elif mode == "Swipe":
            # Swipe approximation: blend controlled by slider.
            try:
                self._layer_a.visible = True
                self._layer_b.visible = True
            except AttributeError:
                pass
            self._apply_opacity()
        else:
            self._apply_opacity()
            self._set_layer_visibility(True)

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
        try:
            showing_a = self._layer_a.visible
            self._set_layer_visibility(not showing_a)
        except AttributeError:
            pass

    def _set_layer_visibility(self, show_a: bool) -> None:
        if self._layer_a is None or self._layer_b is None:
            return
        try:
            self._layer_a.visible = show_a
            self._layer_b.visible = not show_a
        except AttributeError:
            pass

    def _stop_blink_timer(self, *_args) -> None:
        """Stop the auto-blink timer, however this dialog is dismissed.

        Connected to both `finished` (accept()/reject()/Escape - the
        "Close" button's path) and called from `closeEvent` (the native
        close()/window-X-button path), since neither alone covers every
        way this dialog can be dismissed. Unchecking the toggle (rather
        than calling `self._timer.stop()` directly) reuses `_toggle_blink`
        for the text/visibility reset, and is a no-op if blink was never
        started.
        """
        if self._blink_toggle.isChecked():
            self._blink_toggle.setChecked(False)
        self._timer.stop()

    def closeEvent(self, event) -> None:
        self._stop_blink_timer()
        super().closeEvent(event)
