from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from valis_workstation.main_window import MainWindow

logger = logging.getLogger(__name__)


def open_repo_document(
    window: MainWindow, relative_name: str, title: str, log_label: str
) -> None:
    """Open a repository document in the default browser with a unified fallback."""
    doc_path = window._repo_root / relative_name
    if doc_path.exists():
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(doc_path)))
        logger.info("Opened %s: %s", log_label, doc_path.name)
        return
    QtWidgets.QMessageBox.information(
        window,
        title,
        f"{title} not found at {doc_path}",
    )


def open_user_manual(window: MainWindow) -> None:
    """Open the HTML manual in the default browser."""
    open_repo_document(window, "VALIS-GUI-Manual.html", "Manual", "manual")


def open_tutorial(window: MainWindow) -> None:
    """Open the HTML tutorial in the default browser."""
    open_repo_document(window, "VALIS-GUI-Tutorial.html", "Tutorial", "tutorial")


def open_quick_start(window: MainWindow) -> None:
    """Open the quick start guide in the default browser."""
    open_repo_document(window, "QUICK_START.md", "Quick Start", "quick start guide")


def report_issue(window: MainWindow) -> None:
    """Open GitHub issue page."""
    url = "https://github.com/cdgatenbee/valis-wsi/issues/new"
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
    logger.info("Opened GitHub issues page")


def show_about(window: MainWindow) -> None:
    """Show About dialog."""
    about_text = """<h2>VALIS Workstation</h2>
<p><b>Version:</b> 1.0.0</p>
<p><b>Description:</b> Virtual Alignment of pathology Image Series</p>
<p>A GUI application for registering and aligning whole slide images.</p>
<p><b>Based on:</b> VALIS library by Chris Gatenbee</p>
<p><b>License:</b> MIT License</p>
<p><b>GitHub:</b> <a href='https://github.com/cdgatenbee/valis-wsi'>github.com/cdgatenbee/valis-wsi</a></p>
"""
    QtWidgets.QMessageBox.about(window, "About VALIS Workstation", about_text)
