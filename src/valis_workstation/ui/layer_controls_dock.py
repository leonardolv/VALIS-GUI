from __future__ import annotations

from functools import partial

from PySide6 import QtCore, QtWidgets


COLORMAP_OPTIONS = [
    "gray",
    "viridis",
    "magma",
    "inferno",
    "plasma",
    "red",
    "green",
    "blue",
    "cyan",
    "magenta",
]


class LayerControlsDock(QtWidgets.QDockWidget):
    def __init__(self, viewer, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Layers", parent)
        self._viewer = viewer

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Visible", "Name", "Opacity", "Colormap"])
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)
        self.setWidget(container)

        self.refresh()
        self._viewer.layers.events.inserted.connect(lambda *_: self.refresh())
        self._viewer.layers.events.removed.connect(lambda *_: self.refresh())

    def refresh(self) -> None:
        layers = list(self._viewer.layers)
        self._table.setRowCount(len(layers))

        for row_idx, layer in enumerate(layers):
            visible = QtWidgets.QCheckBox()
            visible.setChecked(layer.visible)
            visible.stateChanged.connect(partial(self._toggle_visible, layer))
            self._table.setCellWidget(row_idx, 0, visible)

            name_item = QtWidgets.QTableWidgetItem(layer.name)
            name_item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row_idx, 1, name_item)

            opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            opacity.setRange(0, 100)
            opacity.setValue(int(layer.opacity * 100))
            opacity.valueChanged.connect(partial(self._set_opacity, layer))
            self._table.setCellWidget(row_idx, 2, opacity)

            colormap_combo = QtWidgets.QComboBox()
            colormap_combo.addItems(COLORMAP_OPTIONS)
            current = getattr(layer, "colormap", None)
            if current is not None and hasattr(current, "name") and current.name in COLORMAP_OPTIONS:
                colormap_combo.setCurrentText(current.name)
            colormap_combo.currentTextChanged.connect(partial(self._set_colormap, layer))
            if current is None:
                colormap_combo.setEnabled(False)
            self._table.setCellWidget(row_idx, 3, colormap_combo)

        self._table.resizeColumnsToContents()

    @staticmethod
    def _toggle_visible(layer, state: int) -> None:
        layer.visible = state == QtCore.Qt.CheckState.Checked

    @staticmethod
    def _set_opacity(layer, value: int) -> None:
        layer.opacity = value / 100

    @staticmethod
    def _set_colormap(layer, value: str) -> None:
        if hasattr(layer, "colormap"):
            layer.colormap = value
