from __future__ import annotations

import os
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon


def _is_headless() -> bool:
    """Return True if executing in headless test mode."""
    return (
        os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        or "PYTEST_CURRENT_TEST" in os.environ
    )


class ProjectDock(QtWidgets.QDockWidget):
    count_changed = QtCore.Signal(int)
    open_folder_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Project", parent)
        self.setObjectName("ProjectDock")
        self.setAccessibleName("Project Dock")
        self.setAccessibleDescription("Slide list and project management panel")

        self._slides_header = QtWidgets.QLabel("Slides")
        self._slides_header.setObjectName("projectSlidesHeader")
        self._slides_header.setAccessibleName("Slides Header")
        self._slides_header.setProperty("role", "sidebar-header")

        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setObjectName("projectFilterInput")
        self._filter_edit.setAccessibleName("Filter slides by filename")
        self._filter_edit.setPlaceholderText("Filter by filename...")
        self._filter_edit.setToolTip("Filter loaded slides by name")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._apply_filter)

        self._empty_label = QtWidgets.QLabel(
            "No slides yet.\n\n"
            "Open a folder that contains your slide images "
            "(at least 2 are needed), or drag a folder into the window.\n\n"
            "Supported: TIFF, OME-TIFF, SVS, NDPI, VSI, CZI, SCN, PNG, JPEG."
        )
        self._empty_label.setObjectName("projectEmptyLabel")
        self._empty_label.setAccessibleName("No slides loaded notification")
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #999; font-style: italic; padding: 20px;"
        )
        self._empty_label.setVisible(False)

        self._open_folder_button = QtWidgets.QPushButton("Open Slide Folder…")
        self._open_folder_button.setObjectName("projectOpenFolderBtn")
        self._open_folder_button.setProperty("panelAction", True)
        self._open_folder_button.setToolTip("Choose a folder of slide images (Ctrl+O)")
        self._open_folder_button.setAccessibleName("Open slide folder")
        self._open_folder_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self._open_folder_button.setVisible(False)

        self._list = QtWidgets.QListWidget()
        self._list.setObjectName("projectListWidget")
        self._list.setAccessibleName("Loaded Slide List")
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(QtCore.Qt.MoveAction)
        self._list.setAlternatingRowColors(True)
        # Elide long slide names with "..." instead of pushing layout
        self._list.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

        # Clear all button
        self._clear_button = QtWidgets.QPushButton("Clear All")
        self._clear_button.setObjectName("projectClearAllBtn")
        self._clear_button.setAccessibleName("Clear all slides")
        self._clear_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._clear_button.setIcon(
            load_icon("trash", self, QtWidgets.QStyle.StandardPixmap.SP_TrashIcon)
        )
        self._clear_button.setProperty("panelAction", True)
        self._clear_button.setToolTip("Remove all slides from the project")
        self._clear_button.clicked.connect(self._clear_all_slides)

        self._remove_selected_button = QtWidgets.QPushButton("Remove Selected")
        self._remove_selected_button.setObjectName("projectRemoveSelectedBtn")
        self._remove_selected_button.setAccessibleName("Remove selected slides")
        self._remove_selected_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._remove_selected_button.setIcon(
            load_icon(
                "remove", self, QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton
            )
        )
        self._remove_selected_button.setProperty("panelAction", True)
        self._remove_selected_button.setToolTip("Remove selected slides from the project (Del key). Right-click for options.")
        self._remove_selected_button.clicked.connect(self._remove_selected_slides)
        self._remove_selected_button.setEnabled(False)

        self._delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Delete"), self._list)
        self._delete_shortcut.activated.connect(self._remove_selected_slides)

        self._select_all_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self._list)
        self._select_all_shortcut.activated.connect(self._list.selectAll)

        self._list.itemSelectionChanged.connect(self._update_action_states)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)
        layout.addWidget(self._slides_header)
        layout.addWidget(self._filter_edit)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._open_folder_button)
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

        if _is_headless():
            reply = QtWidgets.QMessageBox.StandardButton.Yes
        else:
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
        self._empty_label.setVisible(total == 0)
        self._open_folder_button.setVisible(total == 0)
        self.count_changed.emit(total)

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

    @property
    def filter_edit(self) -> QtWidgets.QLineEdit:
        """Filter input text line edit."""
        return self._filter_edit

    @property
    def list_widget(self) -> QtWidgets.QListWidget:
        """Project slide list widget."""
        return self._list

    @property
    def clear_button(self) -> QtWidgets.QPushButton:
        """Clear all slides button."""
        return self._clear_button

    @property
    def remove_selected_button(self) -> QtWidgets.QPushButton:
        """Remove selected slides button."""
        return self._remove_selected_button

    @property
    def open_folder_button(self) -> QtWidgets.QPushButton:
        """Open slide folder button."""
        return self._open_folder_button

    @property
    def empty_label(self) -> QtWidgets.QLabel:
        """Notification label shown when slide list is empty."""
        return self._empty_label

    @property
    def slides_header(self) -> QtWidgets.QLabel:
        """Section header label."""
        return self._slides_header

    def slide_count(self) -> int:
        """Return total number of loaded slides."""
        return self._list.count()

    def visible_slide_count(self) -> int:
        """Return number of slides currently visible matching the filter."""
        return self._visible_count()

    def has_slides(self) -> bool:
        """Return True if at least one slide is loaded."""
        return self._list.count() > 0

    def selected_slide_paths(self) -> list[Path]:
        """Return list of paths for currently selected slides."""
        paths: list[Path] = []
        for item in self._list.selectedItems():
            data = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data:
                paths.append(Path(data))
        return paths

    def selected_slide_names(self) -> list[str]:
        """Return list of filenames for currently selected slides."""
        return [item.text() for item in self._list.selectedItems()]

    def select_slide(self, name_or_path: str | Path, clear_others: bool = True) -> bool:
        """Select a slide matching filename or path.

        Parameters
        ----------
        name_or_path : str | Path
            Slide filename or full path string.
        clear_others : bool
            Whether to clear existing selections before selecting.

        Returns
        -------
        bool
            True if slide was found and selected, False otherwise.
        """
        target = str(name_or_path).lower()
        target_name = Path(name_or_path).name.lower()
        found = False
        if clear_others:
            self._list.clearSelection()

        for idx in range(self._list.count()):
            item = self._list.item(idx)
            item_path = str(item.data(QtCore.Qt.ItemDataRole.UserRole) or "").lower()
            item_name = item.text().lower()
            if target == item_path or target == item_name or target_name == item_name:
                item.setSelected(True)
                self._list.setCurrentItem(item)
                found = True
                break
        self._update_action_states()
        return found

    def select_all_slides(self) -> None:
        """Select all slides in the list."""
        self._list.selectAll()
        self._update_action_states()

    def clear_selection(self) -> None:
        """Deselect all slides in the list."""
        self._list.clearSelection()
        self._update_action_states()

    def filter_text(self) -> str:
        """Get current filter text."""
        return self._filter_edit.text()

    def set_filter_text(self, text: str) -> None:
        """Set filter text programmatically."""
        self._filter_edit.setText(text)

    def trigger_open_folder(self) -> None:
        """Programmatically trigger open folder request."""
        self.open_folder_requested.emit()

    def trigger_clear_all(self) -> None:
        """Programmatically trigger clear all slides."""
        self._clear_all_slides()

    def trigger_remove_selected(self) -> None:
        """Programmatically trigger removal of selected slides."""
        self._remove_selected_slides()

