from __future__ import annotations

from pathlib import Path

from PySide6 import QtGui, QtWidgets

_ICON_DIR = Path(__file__).resolve().parent / "icons"


def load_icon(
    name: str,
    widget: QtWidgets.QWidget | None = None,
    fallback: QtWidgets.QStyle.StandardPixmap | None = None,
) -> QtGui.QIcon:
    """Load an SVG icon by *name* with optional style fallback."""
    icon_path = _ICON_DIR / f"{name}.svg"
    if icon_path.exists():
        icon = QtGui.QIcon(str(icon_path))
        if not icon.isNull():
            return icon

    if fallback is not None:
        if widget is not None:
            return widget.style().standardIcon(fallback)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            return app.style().standardIcon(fallback)

    return QtGui.QIcon()
