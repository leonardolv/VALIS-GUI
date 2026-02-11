"""Slide preview panel with thumbnail grid view."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

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
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        # Thumbnail size slider
        toolbar.addWidget(QtWidgets.QLabel("Size:"))
        self._size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._size_slider.setRange(64, 256)
        self._size_slider.setValue(128)
        self._size_slider.setMaximumWidth(150)
        self._size_slider.setToolTip("Adjust thumbnail size")
        self._size_slider.valueChanged.connect(self._update_thumbnail_size)
        toolbar.addWidget(self._size_slider)
        
        toolbar.addStretch()
        
        # View mode toggle
        self._grid_view = QtWidgets.QPushButton("Grid")
        self._grid_view.setCheckable(True)
        self._grid_view.setChecked(True)
        self._grid_view.setToolTip("Grid view")
        
        self._list_view = QtWidgets.QPushButton("List")
        self._list_view.setCheckable(True)
        self._list_view.setToolTip("List view")
        
        view_group = QtWidgets.QButtonGroup(self)
        view_group.addButton(self._grid_view)
        view_group.addButton(self._list_view)
        view_group.buttonClicked.connect(self._toggle_view_mode)
        
        toolbar.addWidget(self._grid_view)
        toolbar.addWidget(self._list_view)
        
        layout.addLayout(toolbar)
        
        # Scroll area for thumbnails
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        self._grid_container = QtWidgets.QWidget()
        self._grid_layout = QtWidgets.QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(8)
        scroll.setWidget(self._grid_container)
        
        layout.addWidget(scroll)
        
        self.setWidget(container)
        
        # Data
        self._thumbnails: dict[str, QtWidgets.QWidget] = {}
        self._current_size = 128
    
    def add_slide(self, name: str, thumbnail: QtGui.QPixmap | None, metadata: dict | None = None) -> None:
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
        # Create thumbnail widget
        widget = QtWidgets.QWidget()
        widget.setObjectName(f"slide_{name}")
        widget_layout = QtWidgets.QVBoxLayout(widget)
        widget_layout.setContentsMargins(4, 4, 4, 4)
        widget_layout.setSpacing(4)
        
        # Thumbnail label
        thumb_label = QtWidgets.QLabel()
        thumb_label.setAlignment(QtCore.Qt.AlignCenter)
        thumb_label.setStyleSheet(
            "QLabel { "
            "border: 2px solid #ccc; "
            "border-radius: 4px; "
            "background: #f5f5f5; "
            "}"
        )
        
        if thumbnail:
            scaled = thumbnail.scaled(
                self._current_size, self._current_size,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            thumb_label.setPixmap(scaled)
        else:
            thumb_label.setText("No preview")
            thumb_label.setMinimumSize(self._current_size, self._current_size)
        
        widget_layout.addWidget(thumb_label)
        
        # Name label
        name_label = QtWidgets.QLabel(name)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(self._current_size + 20)
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
        widget.mousePressEvent = lambda event: self.slide_selected.emit(name)
        widget.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Add to grid
        row = len(self._thumbnails) // 4
        col = len(self._thumbnails) % 4
        self._grid_layout.addWidget(widget, row, col)
        
        self._thumbnails[name] = widget
    
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
            self._reflow_grid()
    
    def clear(self) -> None:
        """Clear all thumbnails."""
        for widget in self._thumbnails.values():
            self._grid_layout.removeWidget(widget)
            widget.deleteLater()
        self._thumbnails.clear()
    
    def _update_thumbnail_size(self, size: int) -> None:
        """Update thumbnail size for all slides.
        
        Parameters
        ----------
        size : int
            New thumbnail size in pixels
        """
        self._current_size = size
        # Could refresh thumbnails here if needed
    
    def _toggle_view_mode(self) -> None:
        """Toggle between grid and list view."""
        if self._list_view.isChecked():
            # Switch to list view (single column)
            self._reflow_grid(columns=1)
        else:
            # Switch to grid view
            self._reflow_grid(columns=4)
    
    def _reflow_grid(self, columns: int = 4) -> None:
        """Reflow the grid layout.
        
        Parameters
        ----------
        columns : int
            Number of columns in grid
        """
        # Remove all widgets
        for widget in self._thumbnails.values():
            self._grid_layout.removeWidget(widget)
        
        # Re-add in new layout
        for i, widget in enumerate(self._thumbnails.values()):
            row = i // columns
            col = i % columns
            self._grid_layout.addWidget(widget, row, col)
