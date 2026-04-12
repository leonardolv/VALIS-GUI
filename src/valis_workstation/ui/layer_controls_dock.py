from __future__ import annotations

import logging

from PySide6 import QtCore, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon

logger = logging.getLogger(__name__)


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
        self.setObjectName("LayerControlsDock")
        self._viewer = viewer

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._layers_header = QtWidgets.QLabel("Layer Controls")
        self._layers_header.setProperty("role", "sidebar-header")
        layout.addWidget(self._layers_header)

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(GRID_SPACING)
        toolbar.addWidget(QtWidgets.QLabel("Search"))
        self._search_edit = QtWidgets.QLineEdit()
        self._search_edit.setPlaceholderText("layer name...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self._search_edit, 1)

        self._lock_check = QtWidgets.QCheckBox("Lock edits")
        self._lock_check.setToolTip(
            "Prevent accidental visibility/opacity/colormap edits"
        )
        toolbar.addWidget(self._lock_check)

        self._solo_btn = QtWidgets.QPushButton("Solo Selected")
        self._solo_btn.setIcon(
            load_icon("play", self, QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
        )
        self._solo_btn.setProperty("panelAction", True)
        self._solo_btn.setToolTip("Show only the selected layer")
        self._solo_btn.clicked.connect(self._solo_selected)
        toolbar.addWidget(self._solo_btn)

        self._reset_opacity_btn = QtWidgets.QPushButton("Reset Opacity")
        self._reset_opacity_btn.setIcon(
            load_icon(
                "refresh", self, QtWidgets.QStyle.StandardPixmap.SP_BrowserReload
            )
        )
        self._reset_opacity_btn.setProperty("panelAction", True)
        self._reset_opacity_btn.setToolTip("Set all visible layers to 100% opacity")
        self._reset_opacity_btn.clicked.connect(self._reset_opacity)
        toolbar.addWidget(self._reset_opacity_btn)

        self._show_all_btn = QtWidgets.QPushButton("Show All")
        self._show_all_btn.setIcon(
            load_icon("eye", self, QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        self._show_all_btn.setProperty("panelAction", True)
        self._show_all_btn.setToolTip("Make all layers visible")
        self._show_all_btn.clicked.connect(self._show_all_layers)
        toolbar.addWidget(self._show_all_btn)
        layout.addLayout(toolbar)

        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Visible", "Name", "Opacity", "Colormap"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(26)
        self._table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table)
        self.setWidget(container)
        self._layers: list = []

        self.refresh()
        self._connect_layer_events()

    def _connect_layer_events(self) -> None:
        """Connect to napari layer events when available.

        Tests and fallback viewers may provide ``layers`` as a plain list,
        so event hooks must be optional.
        """
        layers = getattr(self._viewer, "layers", None)
        events = getattr(layers, "events", None)
        inserted = getattr(events, "inserted", None)
        removed = getattr(events, "removed", None)

        if inserted is not None and hasattr(inserted, "connect"):
            inserted.connect(lambda *_: self.refresh())
        if removed is not None and hasattr(removed, "connect"):
            removed.connect(lambda *_: self.refresh())

    def refresh(self) -> None:
        layers = list(getattr(self._viewer, "layers", []))
        self._layers = layers
        self._table.setRowCount(len(layers))
        logger.debug("Refreshing layer controls: %d layers", len(layers))

        for row_idx, layer in enumerate(layers):
            visible = QtWidgets.QCheckBox()
            visible.setChecked(bool(getattr(layer, "visible", True)))
            visible.stateChanged.connect(
                lambda state, l=layer: self._on_visible_changed(l, state)
            )
            self._table.setCellWidget(row_idx, 0, visible)

            name_item = QtWidgets.QTableWidgetItem(
                str(getattr(layer, "name", "<unnamed>"))
            )
            name_item.setFlags(
                QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
            )
            self._table.setItem(row_idx, 1, name_item)

            opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            opacity.setRange(0, 100)
            opacity_val = float(getattr(layer, "opacity", 1.0))
            opacity.setValue(max(0, min(100, int(opacity_val * 100))))
            opacity.valueChanged.connect(
                lambda value, l=layer: self._on_opacity_changed(l, value)
            )
            self._table.setCellWidget(row_idx, 2, opacity)

            colormap_combo = QtWidgets.QComboBox()
            colormap_combo.addItems(COLORMAP_OPTIONS)
            current = getattr(layer, "colormap", None)
            if (
                current is not None
                and hasattr(current, "name")
                and current.name in COLORMAP_OPTIONS
            ):
                colormap_combo.setCurrentText(current.name)
            colormap_combo.currentTextChanged.connect(
                lambda value, l=layer: self._on_colormap_changed(l, value)
            )
            if current is None:
                colormap_combo.setEnabled(False)
            self._table.setCellWidget(row_idx, 3, colormap_combo)

        self._table.resizeColumnsToContents()
        self._apply_filter()

    def _on_visible_changed(self, layer, state: int) -> None:
        if self._lock_check.isChecked():
            self.refresh()
            return
        self._toggle_visible(layer, state)

    def _on_opacity_changed(self, layer, value: int) -> None:
        if self._lock_check.isChecked():
            self.refresh()
            return
        self._set_opacity(layer, value)

    def _on_colormap_changed(self, layer, value: str) -> None:
        if self._lock_check.isChecked():
            self.refresh()
            return
        self._set_colormap(layer, value)

    def _apply_filter(self) -> None:
        needle = self._search_edit.text().strip().lower()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 1)
            name = item.text().lower() if item else ""
            self._table.setRowHidden(row, bool(needle) and needle not in name)

    def _solo_selected(self) -> None:
        if self._lock_check.isChecked():
            return
        if not self._layers:
            return
        row = self._table.currentRow()
        if row < 0 or self._table.isRowHidden(row):
            row = next(
                (
                    r
                    for r in range(self._table.rowCount())
                    if not self._table.isRowHidden(r)
                ),
                0,
            )
        selected_layer = self._layers[row]
        for layer in self._layers:
            layer.visible = layer is selected_layer
        self.refresh()

    def _reset_opacity(self) -> None:
        if self._lock_check.isChecked():
            return
        for layer in self._layers:
            layer.opacity = 1.0
        self.refresh()

    def _show_all_layers(self) -> None:
        if self._lock_check.isChecked():
            return
        for layer in self._layers:
            layer.visible = True
        self.refresh()

    @staticmethod
    def _toggle_visible(layer, state: int) -> None:
        layer.visible = state == QtCore.Qt.CheckState.Checked.value

    @staticmethod
    def _set_opacity(layer, value: int) -> None:
        layer.opacity = value / 100

    @staticmethod
    def _set_colormap(layer, value: str) -> None:
        if hasattr(layer, "colormap"):
            layer.colormap = value
