from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon


class ProjectDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Project", parent)
        self.setObjectName("ProjectDock")

        self._slides_header = QtWidgets.QLabel("Slides")
        self._slides_header.setProperty("role", "sidebar-header")
        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by filename...")
        self._filter_edit.setToolTip("Filter loaded slides by name")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._apply_filter)

        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(QtCore.Qt.MoveAction)
        self._list.setAlternatingRowColors(True)
        # Elide long slide names with "..." instead of pushing layout
        self._list.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

        # Clear all button
        self._clear_button = QtWidgets.QPushButton("Clear All")
        self._clear_button.setIcon(
            load_icon("trash", self, QtWidgets.QStyle.StandardPixmap.SP_TrashIcon)
        )
        self._clear_button.setProperty("panelAction", True)
        self._clear_button.setToolTip("Remove all slides from the project")
        self._clear_button.clicked.connect(self._clear_all_slides)

        self._remove_selected_button = QtWidgets.QPushButton("Remove Selected")
        self._remove_selected_button.setIcon(
            load_icon(
                "remove", self, QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton
            )
        )
        self._remove_selected_button.setProperty("panelAction", True)
        self._remove_selected_button.setToolTip("Remove selected slides (Del)")
        self._remove_selected_button.clicked.connect(self._remove_selected_slides)
        self._remove_selected_button.setEnabled(False)

        self._delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Delete"), self._list)
        self._delete_shortcut.activated.connect(self._remove_selected_slides)

        self._list.itemSelectionChanged.connect(self._update_action_states)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)
        layout.addWidget(self._slides_header)
        layout.addWidget(self._filter_edit)
        layout.addWidget(self._list)

        actions_row = QtWidgets.QHBoxLayout()
        actions_row.setSpacing(GRID_SPACING)
        actions_row.addWidget(self._remove_selected_button)
        actions_row.addWidget(self._clear_button)
        layout.addLayout(actions_row)
        self.setWidget(container)

        self._update_title()

    def set_slides(self, slides: list[Path]) -> None:
        self._list.clear()
        for slide in slides:
            item = QtWidgets.QListWidgetItem(slide.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(slide))
            item.setToolTip(str(slide))  # Full path on hover
            self._list.addItem(item)
        self._apply_filter()
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
            self,
            "Clear All Slides",
            f"Remove all {self._list.count()} slides from the project?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._list.clear()
            self._filter_edit.clear()
            self._update_title()

    def _remove_selected_slides(self) -> None:
        """Remove currently selected slides from the list."""
        selected = self._list.selectedItems()
        if not selected:
            return
        for item in selected:
            row = self._list.row(item)
            self._list.takeItem(row)
        self._update_title()

    def _apply_filter(self) -> None:
        """Filter slides by name without mutating project order."""
        needle = self._filter_edit.text().strip().lower()
        for idx in range(self._list.count()):
            item = self._list.item(idx)
            name = item.text().lower()
            item.setHidden(bool(needle) and needle not in name)
        self._update_title()

    def _visible_count(self) -> int:
        visible = 0
        for idx in range(self._list.count()):
            if not self._list.item(idx).isHidden():
                visible += 1
        return visible

    def _update_title(self) -> None:
        """Update dock title with slide count."""
        total = self._list.count()
        visible = self._visible_count()
        self._update_action_states()
        self._clear_button.setEnabled(total > 0)

        if total == 0:
            self.setWindowTitle("Project")
        elif visible != total:
            self.setWindowTitle(
                f"Project ({visible}/{total} slide{'s' if total != 1 else ''})"
            )
        else:
            self.setWindowTitle(
                f"Project ({total} slide{'s' if total != 1 else ''})"
            )

    def _update_action_states(self) -> None:
        has_selection = len(self._list.selectedItems()) > 0
        self._remove_selected_button.setEnabled(has_selection)
