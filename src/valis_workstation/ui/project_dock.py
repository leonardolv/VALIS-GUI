from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets


class ProjectDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Project", parent)
        self.setObjectName("ProjectDock")
        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(QtCore.Qt.MoveAction)
        self._list.setAlternatingRowColors(True)

        # Clear all button
        self._clear_button = QtWidgets.QPushButton("Clear All")
        self._clear_button.setToolTip("Remove all slides from the project")
        self._clear_button.clicked.connect(self._clear_all_slides)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(self._list)
        layout.addWidget(self._clear_button)
        self.setWidget(container)
        
        self._update_title()

    def set_slides(self, slides: list[Path]) -> None:
        self._list.clear()
        for slide in slides:
            item = QtWidgets.QListWidgetItem(slide.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(slide))
            self._list.addItem(item)
        self._update_title()

    def slides(self) -> list[Path]:
        paths: list[Path] = []
        for idx in range(self._list.count()):
            item = self._list.item(idx)
            paths.append(Path(item.data(QtCore.Qt.ItemDataRole.UserRole)))
        return paths

    def _clear_all_slides(self) -> None:
        """Clear all slides from the list."""
        if self._list.count() == 0:
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Clear All Slides",
            f"Remove all {self._list.count()} slides from the project?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._list.clear()
            self._update_title()

    def _update_title(self) -> None:
        """Update dock title with slide count."""
        count = self._list.count()
        if count == 0:
            self.setWindowTitle("Project")
        else:
            self.setWindowTitle(f"Project ({count} slide{'s' if count != 1 else ''})")
