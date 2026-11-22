"""Slide preview panel with thumbnail grid view."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon


class SlidePreviewDock(QtWidgets.QDockWidget):
    """Dock widget displaying slide thumbnails and metadata.

    Shows a grid of slide thumbnails with metadata tooltips, allowing users
    to quickly preview and verify loaded slides.
    """

    slide_selected = QtCore.Signal(str)  # Emitted when a slide is clicked
    count_changed = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Slide Preview", parent)
        self.setObjectName("SlidePreviewDock")
        self.setAccessibleName("Slide Preview Dock")
        self.setAccessibleDescription(
            "Slide preview dock displaying slide thumbnails and metadata cards in responsive grid or list layout."
        )

        # Main container
        container = QtWidgets.QWidget()
        container.setObjectName("slidePreviewContainer")
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._slides_header = QtWidgets.QLabel("Thumbnails")
        self._slides_header.setObjectName("slidePreviewHeader")
        self._slides_header.setAccessibleName("Slide Preview Header")
        self._slides_header.setProperty("role", "sidebar-header")
        layout.addWidget(self._slides_header)

        # Toolbar
        # Two rows: one row of seven controls cannot fit a ~240px sidebar
        # (the filter box collapsed to "slid..." and the slider vanished).
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(GRID_SPACING)
        toolbar2 = QtWidgets.QHBoxLayout()
        toolbar2.setSpacing(GRID_SPACING)

        filter_label = QtWidgets.QLabel("Filter:")
        filter_label.setObjectName("slideFilterLabel")
        toolbar.addWidget(filter_label)

        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setObjectName("slideFilterEdit")
        self._filter_edit.setAccessibleName("Filter Slide Thumbnails")
        self._filter_edit.setAccessibleDescription("Filter visible slide thumbnails by filename.")
        self._filter_edit.setPlaceholderText("slide name...")
        self._filter_edit.setToolTip("Filter thumbnails by filename")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._apply_filter_sort)
        self._filter_edit.setMinimumWidth(80)
        toolbar.addWidget(self._filter_edit, 1)

        sort_label = QtWidgets.QLabel("Sort:")
        sort_label.setObjectName("slideSortLabel")
        toolbar.addWidget(sort_label)

        self._sort_combo = QtWidgets.QComboBox()
        self._sort_combo.setObjectName("slideSortCombo")
        self._sort_combo.setAccessibleName("Sort Slide Thumbnails")
        self._sort_combo.setAccessibleDescription("Sort order for slide thumbnails (Name A-Z or Name Z-A).")
        self._sort_combo.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._sort_combo.addItems(["Name (A-Z)", "Name (Z-A)"])
        self._sort_combo.setToolTip("Sort order for thumbnails")
        self._sort_combo.currentTextChanged.connect(self._apply_filter_sort)
        toolbar.addWidget(self._sort_combo)

        # Thumbnail size slider
        size_label = QtWidgets.QLabel("Size:")
        size_label.setObjectName("slideSizeLabel")
        toolbar2.addWidget(size_label)

        self._size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._size_slider.setObjectName("slideSizeSlider")
        self._size_slider.setAccessibleName("Thumbnail Size Slider")
        self._size_slider.setAccessibleDescription("Adjust thumbnail preview size from 64 to 256 pixels.")
        self._size_slider.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._size_slider.setRange(64, 256)
        self._size_slider.setValue(128)
        self._size_slider.setMaximumWidth(150)
        self._size_slider.setToolTip("Thumbnail size (64-256 px)")
        self._size_slider.valueChanged.connect(self._update_thumbnail_size)
        toolbar2.addWidget(self._size_slider, 1)

        self._summary_label = QtWidgets.QLabel("0 slides")
        self._summary_label.setObjectName("slideSummaryLabel")
        self._summary_label.setAccessibleName("Slide Count Summary")
        self._summary_label.setProperty("role", "sidebar-subtle")
        toolbar2.addWidget(self._summary_label)

        # View mode toggle
        self._grid_view = QtWidgets.QPushButton("Grid")
        self._grid_view.setObjectName("slideGridViewBtn")
        self._grid_view.setIcon(
            load_icon(
                "grid", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self._grid_view.setProperty("viewToggle", True)
        self._grid_view.setCheckable(True)
        self._grid_view.setChecked(True)
        self._grid_view.setToolTip("Show thumbnails in a responsive grid")
        self._grid_view.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._list_view = QtWidgets.QPushButton("List")
        self._list_view.setObjectName("slideListViewBtn")
        self._list_view.setIcon(
            load_icon("list", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView)
        )
        self._list_view.setProperty("viewToggle", True)
        self._list_view.setCheckable(True)
        self._list_view.setToolTip("Show one thumbnail row per line")
        self._list_view.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        view_group = QtWidgets.QButtonGroup(self)
        view_group.setObjectName("slideViewGroup")
        view_group.setExclusive(True)
        view_group.addButton(self._grid_view)
        view_group.addButton(self._list_view)
        view_group.buttonClicked.connect(self._toggle_view_mode)

        # Icon-only (tooltips name them): text labels clipped the "List"
        # button off the edge of the narrow sidebar.
        for _btn, _name in ((self._grid_view, "Grid view"), (self._list_view, "List view")):
            _btn.setText("")
            _btn.setAccessibleName(_name)
            _btn.setAccessibleDescription(f"Switch thumbnails to {_name.lower()}.")
        self._size_slider.setMinimumWidth(50)
        toolbar2.addWidget(self._grid_view)
        toolbar2.addWidget(self._list_view)

        layout.addLayout(toolbar)
        layout.addLayout(toolbar2)

        # Scroll area for thumbnails
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setObjectName("slideScrollArea")
        self._scroll.setAccessibleName("Slide Thumbnails Scroll Area")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self._grid_container = QtWidgets.QWidget()
        self._grid_container.setObjectName("slideGridContainer")
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

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
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
        widget.setAccessibleName(f"Slide Card: {name}")
        widget.setAccessibleDescription(f"Thumbnail card for slide {name}. Click to select.")
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
        thumb_label.setAccessibleName(f"Thumbnail image for {name}")
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
        name_label.setAccessibleName(f"Slide filename: {name}")
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
            names.sort(key=lambda n: (n.lower(), n), reverse=True)
        else:
            names.sort(key=lambda n: (n.lower(), n))

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

    def slide_count(self) -> int:
        """Return total number of loaded slide thumbnails."""
        return len(self._thumbnails)

    def _update_summary(self) -> None:
        total = len(self._thumbnails)
        self.count_changed.emit(total)
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

    # ── Public widget properties ──────────────────────────────────────

    @property
    def header_label(self) -> QtWidgets.QLabel:
        """Header label widget."""
        return self._slides_header

    @property
    def filter_edit(self) -> QtWidgets.QLineEdit:
        """Filter line edit control."""
        return self._filter_edit

    @property
    def sort_combobox(self) -> QtWidgets.QComboBox:
        """Sort mode combo box."""
        return self._sort_combo

    @property
    def size_slider(self) -> QtWidgets.QSlider:
        """Thumbnail size slider."""
        return self._size_slider

    @property
    def summary_label(self) -> QtWidgets.QLabel:
        """Slide count summary label."""
        return self._summary_label

    @property
    def grid_view_button(self) -> QtWidgets.QPushButton:
        """Grid view mode toggle button."""
        return self._grid_view

    @property
    def list_view_button(self) -> QtWidgets.QPushButton:
        """List view mode toggle button."""
        return self._list_view

    @property
    def scroll_area(self) -> QtWidgets.QScrollArea:
        """Thumbnail scroll area container."""
        return self._scroll

    @property
    def grid_container(self) -> QtWidgets.QWidget:
        """Internal container widget holding thumbnail grid."""
        return self._grid_container

    # ── Ergonomic state queries and setters ────────────────────────────

    def has_slides(self) -> bool:
        """Return True if any slide thumbnails are loaded."""
        return len(self._thumbnails) > 0

    def slide_names(self) -> list[str]:
        """Return list of loaded slide names in ingestion order."""
        return list(self._thumbnails.keys())

    def visible_slide_count(self) -> int:
        """Return number of currently visible slide thumbnails matching filter."""
        return sum(
            1
            for widget in self._thumbnails.values()
            if bool(widget.property("filterVisible"))
        )

    def visible_slide_names(self) -> list[str]:
        """Return list of visible slide names matching filter in current sort order."""
        needle = self._filter_edit.text().strip().lower()
        names = list(self._thumbnails.keys())
        if self._sort_combo.currentText() == "Name (Z-A)":
            names.sort(key=lambda n: (n.lower(), n), reverse=True)
        else:
            names.sort(key=lambda n: (n.lower(), n))
        return [
            name
            for name in names
            if needle in name.lower()
            and bool(self._thumbnails[name].property("filterVisible"))
        ]

    def selected_slide_name(self) -> str | None:
        """Return name of currently selected slide, or None if none selected."""
        return self._selected_slide

    def is_slide_selected(self, name: str) -> bool:
        """Return True if specified slide is currently selected."""
        return self._selected_slide == name

    def select_slide(self, name: str | None) -> bool:
        """Programmatically select a slide by name.

        Parameters
        ----------
        name : str | None
            Slide name to select, or None to deselect.

        Returns
        -------
        bool
            True if slide selection was updated, False if slide name was not found.
        """
        if name is None:
            self._set_selected_slide(None)
            return True
        if name not in self._thumbnails:
            return False
        self._on_slide_clicked(name)
        return True

    def filter_text(self) -> str:
        """Return current filter query text."""
        return self._filter_edit.text()

    def set_filter_text(self, text: str) -> None:
        """Update filter query text and trigger filtering."""
        self._filter_edit.setText(text)

    def clear_filter(self) -> None:
        """Clear filter query text."""
        self._filter_edit.clear()

    def sort_mode(self) -> str:
        """Return current sort order mode text."""
        return self._sort_combo.currentText()

    def set_sort_mode(self, mode: str) -> bool:
        """Set thumbnail sort order mode ('Name (A-Z)' or 'Name (Z-A)')."""
        idx = self._sort_combo.findText(mode)
        if idx >= 0:
            self._sort_combo.setCurrentIndex(idx)
            return True
        return False

    def thumbnail_size(self) -> int:
        """Return current thumbnail size in pixels."""
        return self._current_size

    def set_thumbnail_size(self, size: int) -> None:
        """Set thumbnail size in pixels (clamped between 64 and 256)."""
        self._size_slider.setValue(size)

    def is_grid_view(self) -> bool:
        """Return True if grid view mode is active."""
        return self._grid_view.isChecked()

    def is_list_view(self) -> bool:
        """Return True if list view mode is active."""
        return self._list_view.isChecked()

    def set_view_mode(self, mode: str) -> bool:
        """Set view mode to 'grid' or 'list'.

        Returns
        -------
        bool
            True if mode was recognized and applied, False otherwise.
        """
        normalized = mode.strip().lower()
        if normalized == "grid":
            if not self._grid_view.isChecked():
                self._grid_view.click()
            return True
        elif normalized == "list":
            if not self._list_view.isChecked():
                self._list_view.click()
            return True
        return False

    def summary_text(self) -> str:
        """Return slide count summary text."""
        return self._summary_label.text()

    def slide_metadata(self, name: str) -> dict | None:
        """Return metadata dictionary for the specified slide, or None."""
        data = self._slide_data.get(name)
        return data.get("metadata") if data else None

    def slide_widget(self, name: str) -> QtWidgets.QWidget | None:
        """Return thumbnail card widget for the specified slide, or None."""
        return self._thumbnails.get(name)

    def slide_pixmap(self, name: str) -> QtGui.QPixmap | None:
        """Return thumbnail pixmap for the specified slide, or None."""
        data = self._slide_data.get(name)
        return data.get("thumbnail") if data else None

    # ── Programmatic action triggers ───────────────────────────────────

    def trigger_grid_view(self) -> None:
        """Programmatically switch to grid view mode."""
        if not self._grid_view.isChecked():
            self._grid_view.click()

    def trigger_list_view(self) -> None:
        """Programmatically switch to list view mode."""
        if not self._list_view.isChecked():
            self._list_view.click()

    def trigger_select_next(self) -> bool:
        """Programmatically select the next visible slide in order."""
        visible = self.visible_slide_names()
        if not visible:
            return False
        if self._selected_slide not in visible:
            return self.select_slide(visible[0])
        idx = visible.index(self._selected_slide)
        next_idx = (idx + 1) % len(visible)
        return self.select_slide(visible[next_idx])

    def trigger_select_previous(self) -> bool:
        """Programmatically select the previous visible slide in order."""
        visible = self.visible_slide_names()
        if not visible:
            return False
        if self._selected_slide not in visible:
            return self.select_slide(visible[-1])
        idx = visible.index(self._selected_slide)
        prev_idx = (idx - 1) % len(visible)
        return self.select_slide(visible[prev_idx])

    def trigger_clear(self) -> None:
        """Programmatically clear all slide thumbnails."""
        self.clear()

