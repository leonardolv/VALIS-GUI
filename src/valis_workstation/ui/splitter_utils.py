"""Splitter persistence and resizing helpers.

Provides utilities to save/restore ``QSplitter`` sizes via
``QSettings`` and programmatic helpers for common layout operations.

Includes :class:`GripSplitterHandle` and :class:`GripSplitter` for
painting visible drag-grip indicators on splitter handles.
"""

from __future__ import annotations

import logging
from typing import Sequence

from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)

_SETTINGS_ORG = "VALIS"
_SETTINGS_APP = "Workstation"


def _settings() -> QtCore.QSettings:
    return QtCore.QSettings(_SETTINGS_ORG, _SETTINGS_APP)


# ── Custom grip-handle splitter ────────────────────────────────


class GripSplitterHandle(QtWidgets.QSplitterHandle):
    """A splitter handle that paints a row/column of grip dots.

    The dots give the user a clear visual affordance that the handle
    can be dragged to resize neighbouring panels.
    """

    _DOT_RADIUS: int = 1
    _DOT_SPACING: int = 4
    _DOT_COUNT: int = 5
    _DOT_COLOR = QtGui.QColor(140, 140, 140, 200)
    _HOVER_COLOR = QtGui.QColor(180, 180, 180, 240)

    def __init__(
        self,
        orientation: QtCore.Qt.Orientation,
        parent: QtWidgets.QSplitter,
    ) -> None:
        super().__init__(orientation, parent)
        self._hovered = False
        self.setMouseTracking(True)

    # -- events ---------------------------------------------------

    def enterEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # -- painting -------------------------------------------------

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        color = self._HOVER_COLOR if self._hovered else self._DOT_COLOR
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(color)

        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()

        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            # Vertical column of dots
            total_h = (self._DOT_COUNT - 1) * self._DOT_SPACING
            start_y = cy - total_h // 2
            for i in range(self._DOT_COUNT):
                y = start_y + i * self._DOT_SPACING
                painter.drawEllipse(
                    QtCore.QPointF(cx, y),
                    self._DOT_RADIUS,
                    self._DOT_RADIUS,
                )
        else:
            # Horizontal row of dots
            total_w = (self._DOT_COUNT - 1) * self._DOT_SPACING
            start_x = cx - total_w // 2
            for i in range(self._DOT_COUNT):
                x = start_x + i * self._DOT_SPACING
                painter.drawEllipse(
                    QtCore.QPointF(x, cy),
                    self._DOT_RADIUS,
                    self._DOT_RADIUS,
                )

        painter.end()


class GripSplitter(QtWidgets.QSplitter):
    """A ``QSplitter`` that uses :class:`GripSplitterHandle`.

    Drop-in replacement for ``QSplitter``.  All handles created by
    this widget will paint visible grip dots and show appropriate
    resize cursors and tooltips automatically.
    """

    def __init__(
        self,
        orientation: QtCore.Qt.Orientation,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)

    def createHandle(self) -> QtWidgets.QSplitterHandle:  # noqa: N802
        handle = GripSplitterHandle(self.orientation(), self)
        # Set appropriate cursor
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            handle.setCursor(QtCore.Qt.CursorShape.SplitHCursor)
        else:
            handle.setCursor(QtCore.Qt.CursorShape.SplitVCursor)
        handle.setToolTip("Drag to resize panels")
        return handle


# ── Persistence ────────────────────────────────────────────────

def persist_splitter_state(splitter: QtWidgets.QSplitter, key: str) -> None:
    """Save *splitter* sizes to ``QSettings`` under *key*."""
    settings = _settings()
    settings.setValue(key, splitter.sizes())
    logger.debug("Saved splitter state: %s = %s", key, splitter.sizes())


def restore_splitter_state(
    splitter: QtWidgets.QSplitter,
    key: str,
    default_sizes: Sequence[int] | None = None,
) -> bool:
    """Restore *splitter* sizes from ``QSettings``.

    Returns ``True`` if a stored value was found and applied, ``False``
    if *default_sizes* (or nothing) was used.
    """
    settings = _settings()
    raw = settings.value(key)
    if raw is not None:
        try:
            sizes = [int(v) for v in raw]
            if len(sizes) == splitter.count():
                splitter.setSizes(sizes)
                logger.debug("Restored splitter state: %s = %s", key, sizes)
                return True
            logger.warning(
                "Stored splitter sizes count mismatch for %s: expected %d, got %d",
                key, splitter.count(), len(sizes),
            )
        except (TypeError, ValueError):
            logger.warning("Invalid stored splitter sizes for %s: %r", key, raw)

    if default_sizes is not None:
        splitter.setSizes(list(default_sizes))
    return False


def clear_splitter_state(key: str) -> None:
    """Remove persisted splitter state for *key*."""
    settings = _settings()
    settings.remove(key)
    logger.debug("Cleared splitter state: %s", key)


# ── Programmatic resizing ──────────────────────────────────────

def set_splitter_sizes(
    splitter: QtWidgets.QSplitter, sizes: Sequence[int]
) -> None:
    """Set *splitter* sizes with bounds validation."""
    if len(sizes) != splitter.count():
        raise ValueError(
            f"Expected {splitter.count()} sizes, got {len(sizes)}"
        )
    splitter.setSizes(list(sizes))


def collapse_panel(
    splitter: QtWidgets.QSplitter, index: int, min_size: int = 0
) -> None:
    """Collapse panel at *index* to *min_size* and redistribute space."""
    sizes = splitter.sizes()
    if index < 0 or index >= len(sizes):
        return
    freed = sizes[index] - min_size
    sizes[index] = min_size
    # Distribute freed space to the largest neighbour
    if freed > 0:
        largest_idx = max(
            (i for i in range(len(sizes)) if i != index),
            key=lambda i: sizes[i],
        )
        sizes[largest_idx] += freed
    splitter.setSizes(sizes)


def expand_panel(
    splitter: QtWidgets.QSplitter,
    index: int,
    target_size: int,
) -> None:
    """Expand panel at *index* to *target_size*, shrinking neighbours."""
    sizes = splitter.sizes()
    if index < 0 or index >= len(sizes):
        return
    delta = target_size - sizes[index]
    if delta <= 0:
        return
    sizes[index] = target_size
    # Shrink the largest neighbour
    largest_idx = max(
        (i for i in range(len(sizes)) if i != index),
        key=lambda i: sizes[i],
    )
    sizes[largest_idx] = max(0, sizes[largest_idx] - delta)
    splitter.setSizes(sizes)
