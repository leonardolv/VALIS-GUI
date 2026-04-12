"""Slide preview panel with thumbnail grid view."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon

if TYPE_CHECKING:
    pass


class SlidePreviewDock(QtWidgets.QDockWidget):
    """Dock widget displaying slide thumbnails and metadata.

    Shows a grid of slide thumbnails with metadata tooltips, allowing users
    to quickly preview and verify loaded slides.
    """

    slide_selected = QtCore.Signal(str)  # Emitted when a slide is clicked

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Slide Preview", parent)
        self.setObjectName("SlidePreviewDock")

        # Main container
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._slides_header = QtWidgets.QLabel("Thumbnails")
        self._slides_header.setProperty("role", "sidebar-header")
        layout.addWidget(self._slides_header)

        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(GRID_SPACING)

        toolbar.addWidget(QtWidgets.QLabel("Filter:"))
        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setPlaceholderText("slide name...")
        self._filter_edit.setToolTip("Filter thumbnails by slide name")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._apply_filter_sort)
        self._filter_edit.setMaximumWidth(220)
        toolbar.addWidget(self._filter_edit)

        toolbar.addWidget(QtWidgets.QLabel("Sort:"))
        self._sort_combo = QtWidgets.QComboBox()
        self._sort_combo.addItems(["Name (A-Z)", "Name (Z-A)"])
        self._sort_combo.currentTextChanged.connect(self._apply_filter_sort)
        toolbar.addWidget(self._sort_combo)

        # Thumbnail size slider
        toolbar.addWidget(QtWidgets.QLabel("Size:"))
        self._size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._size_slider.setRange(64, 256)
        self._size_slider.setValue(128)
        self._size_slider.setMaximumWidth(150)
        self._size_slider.setToolTip("Adjust thumbnail size")
        self._size_slider.valueChanged.connect(self._update_thumbnail_size)
        toolbar.addWidget(self._size_slider)

        self._summary_label = QtWidgets.QLabel("0 slides")
        self._summary_label.setProperty("role", "sidebar-subtle")
        toolbar.addWidget(self._summary_label)

        toolbar.addStretch()

        # View mode toggle
        self._grid_view = QtWidgets.QPushButton("Grid")
        self._grid_view.setIcon(
            load_icon(
                "grid", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self._grid_view.setProperty("viewToggle", True)
        self._grid_view.setCheckable(True)
        self._grid_view.setChecked(True)
        self._grid_view.setToolTip("Show thumbnails in a responsive grid")

        self._list_view = QtWidgets.QPushButton("List")
        self._list_view.setIcon(
            load_icon("list", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView)
        )
        self._list_view.setProperty("viewToggle", True)
        self._list_view.setCheckable(True)
        self._list_view.setToolTip("Show one thumbnail row per line")

        view_group = QtWidgets.QButtonGroup(self)
        view_group.setExclusive(True)
        view_group.addButton(self._grid_view)
        view_group.addButton(self._list_view)
        view_group.buttonClicked.connect(self._toggle_view_mode)

        toolbar.addWidget(self._grid_view)
        toolbar.addWidget(self._list_view)

        layout.addLayout(toolbar)

        # Scroll area for thumbnails
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self._grid_container = QtWidgets.QWidget()
        self._grid_layout = QtWidgets.QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(GRID_SPACING)
        self._grid_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self._scroll.setWidget(self._grid_container)
        self._scroll.viewport().installEventFilter(self)

        layout.addWidget(self._scroll)

        self.setWidget(container)

        # Data
        self._thumbnails: dict[str, QtWidgets.QWidget] = {}
        self._slide_data: dict[str, dict] = {}
        self._current_size = 128
        self._selected_slide: str | None = None

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802
        if (
            watched is self._scroll.viewport()
            and event.type() == QtCore.QEvent.Type.Resize
        ):
            self._reflow_grid()
        return super().eventFilter(watched, event)

    def _column_count_for_width(self) -> int:
        """Choose a grid column count that fits the current viewport width."""
        if self._list_view.isChecked():
            return 1

        viewport_w = max(1, self._scroll.viewport().width())
        tile_w = max(96, self._current_size + 28)
        return max(1, viewport_w // tile_w)

    def add_slide(
        self, name: str, thumbnail: QtGui.QPixmap | None, metadata: dict | None = None
    ) -> None:
        """Add a slide thumbnail to the preview.

        Parameters
        ----------
        name : str
            Slide name
        thumbnail : QtGui.QPixmap | None
            Thumbnail image (will be scaled)
        metadata : dict | None
            Slide metadata for tooltip
        """
        if name in self._thumbnails:
            self.remove_slide(name)

        # Create thumbnail widget
        widget = QtWidgets.QWidget()
        widget.setObjectName("SlideCard")
        widget.setProperty("selected", False)
        widget.setProperty("filterVisible", True)
        widget.setProperty("slideName", name)
        widget_layout = QtWidgets.QVBoxLayout(widget)
        widget_layout.setContentsMargins(
            GRID_SPACING // 2,
            GRID_SPACING // 2,
            GRID_SPACING // 2,
            GRID_SPACING // 2,
        )
        widget_layout.setSpacing(GRID_SPACING // 2)

        # Thumbnail label
        thumb_label = QtWidgets.QLabel()
        thumb_label.setObjectName("SlideThumb")
        thumb_label.setAlignment(QtCore.Qt.AlignCenter)
        thumb_label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        if thumbnail:
            scaled = thumbnail.scaled(
                self._current_size,
                self._current_size,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            thumb_label.setPixmap(scaled)
        else:
            thumb_label.setText("No preview")
            thumb_label.setMinimumSize(self._current_size, self._current_size)

        widget_layout.addWidget(thumb_label)

        # Name label
        name_label = QtWidgets.QLabel(name)
        name_label.setObjectName("SlideName")
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(self._current_size + 20)
        name_label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        font = name_label.font()
        font.setPointSize(8)
        name_label.setFont(font)
        widget_layout.addWidget(name_label)

        # Build tooltip from metadata
        if metadata:
            tooltip_parts = [f"<b>{name}</b>"]
            if "dimensions" in metadata:
                w, h = metadata["dimensions"]
                tooltip_parts.append(f"Size: {w} × {h} pixels")
            if "dtype" in metadata:
                tooltip_parts.append(f"Type: {metadata['dtype']}")
            if "channels" in metadata:
                tooltip_parts.append(f"Channels: {metadata['channels']}")
            if "file_path" in metadata:
                path = Path(metadata["file_path"])
                tooltip_parts.append(f"File: {path.name}")
            widget.setToolTip("<br>".join(tooltip_parts))
        else:
            widget.setToolTip(name)

        # Make clickable
        widget.mousePressEvent = lambda event, n=name: self._on_slide_clicked(n)
        widget.setCursor(QtCore.Qt.PointingHandCursor)

        self._thumbnails[name] = widget
        self._slide_data[name] = {
            "widget": widget,
            "thumbnail": thumbnail,
            "metadata": metadata or {},
            "thumb_label": thumb_label,
            "name_label": name_label,
        }
        self._apply_filter_sort()
        self._update_summary()

    def remove_slide(self, name: str) -> None:
        """Remove a slide thumbnail.

        Parameters
        ----------
        name : str
            Slide name to remove
        """
        if name in self._thumbnails:
            widget = self._thumbnails.pop(name)
            self._grid_layout.removeWidget(widget)
            widget.deleteLater()
            self._slide_data.pop(name, None)
            if self._selected_slide == name:
                self._selected_slide = None
            self._reflow_grid()
            self._update_summary()

    def clear(self) -> None:
        """Clear all thumbnails."""
        for widget in self._thumbnails.values():
            self._grid_layout.removeWidget(widget)
            widget.deleteLater()
        self._thumbnails.clear()
        self._slide_data.clear()
        self._selected_slide = None
        self._update_summary()

    def _on_slide_clicked(self, name: str) -> None:
        self._set_selected_slide(name)
        self.slide_selected.emit(name)

    def _set_selected_slide(self, name: str | None) -> None:
        self._selected_slide = name
        for slide_name, widget in self._thumbnails.items():
            widget.setProperty("selected", slide_name == name)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _update_thumbnail_size(self, size: int) -> None:
        """Update thumbnail size for all slides.

        Parameters
        ----------
        size : int
            New thumbnail size in pixels
        """
        self._current_size = size
        for data in self._slide_data.values():
            thumb_label = data["thumb_label"]
            thumb = data["thumbnail"]
            if isinstance(thumb, QtGui.QPixmap) and not thumb.isNull():
                scaled = thumb.scaled(
                    self._current_size,
                    self._current_size,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
                thumb_label.setPixmap(scaled)
            else:
                thumb_label.setMinimumSize(self._current_size, self._current_size)
            data["name_label"].setMaximumWidth(self._current_size + 20)
        self._reflow_grid()

    def _toggle_view_mode(self) -> None:
        """Toggle between grid and list view."""
        self._reflow_grid()

    def _reflow_grid(self, columns: int | None = None) -> None:
        """Reflow the grid layout.

        Parameters
        ----------
        columns : int | None
            Number of columns in grid. If None, computed from viewport width.
        """
        if columns is None:
            columns = self._column_count_for_width()

        # Remove all widgets
        for widget in self._thumbnails.values():
            self._grid_layout.removeWidget(widget)

        # Re-add in new layout
        visible_names = [
            name for name, widget in self._thumbnails.items() if widget.isVisible()
        ]
        for i, name in enumerate(visible_names):
            widget = self._thumbnails[name]
            row = i // columns
            col = i % columns
            self._grid_layout.addWidget(widget, row, col)

    def _apply_filter_sort(self) -> None:
        """Apply name filter and ordering to thumbnail widgets."""
        needle = self._filter_edit.text().strip().lower()

        names = list(self._thumbnails.keys())
        if self._sort_combo.currentText() == "Name (Z-A)":
            names.sort(reverse=True)
        else:
            names.sort()

        # Ensure layout is rebuilt in the sorted order.
        for widget in self._thumbnails.values():
            self._grid_layout.removeWidget(widget)

        visible_widgets: list[QtWidgets.QWidget] = []
        for name in names:
            widget = self._thumbnails[name]
            is_visible = needle in name.lower()
            widget.setProperty("filterVisible", is_visible)
            widget.setVisible(is_visible)
            if is_visible:
                visible_widgets.append(widget)

        columns = self._column_count_for_width()
        for i, widget in enumerate(visible_widgets):
            row = i // columns
            col = i % columns
            self._grid_layout.addWidget(widget, row, col)
        self._update_summary()

    def _update_summary(self) -> None:
        total = len(self._thumbnails)
        visible = sum(
            1
            for widget in self._thumbnails.values()
            if bool(widget.property("filterVisible"))
        )

        if total == 0:
            self._summary_label.setText("0 slides")
            self.setWindowTitle("Slide Preview")
        elif visible != total:
            self._summary_label.setText(f"{visible}/{total} visible")
            self.setWindowTitle(f"Slide Preview ({visible}/{total})")
        else:
            self._summary_label.setText(f"{total} slides")
            self.setWindowTitle(f"Slide Preview ({total})")
