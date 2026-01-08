from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets


class ProjectDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Project", parent)
        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(QtCore.Qt.MoveAction)
        self._list.setAlternatingRowColors(True)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(self._list)
        self.setWidget(container)

    def set_slides(self, slides: list[Path]) -> None:
        self._list.clear()
        for slide in slides:
            item = QtWidgets.QListWidgetItem(slide.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(slide))
            self._list.addItem(item)

    def slides(self) -> list[Path]:
        paths: list[Path] = []
        for idx in range(self._list.count()):
            item = self._list.item(idx)
            paths.append(Path(item.data(QtCore.Qt.ItemDataRole.UserRole)))
        return paths
