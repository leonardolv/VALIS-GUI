"""Enhanced error dialog with detailed information and copy-to-clipboard functionality."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class ErrorDetailDialog(QtWidgets.QDialog):
    """Dialog showing detailed error information with copy-to-clipboard capability."""

    def __init__(
        self,
        error_message: str,
        technical_details: str = "",
        log_excerpt: str = "",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Error Details")
        self.resize(700, 500)

        layout = QtWidgets.QVBoxLayout(self)

        # User-friendly message
        self.message_label = QtWidgets.QLabel("<h3>An error occurred:</h3>")
        layout.addWidget(self.message_label)

        self.error_text = QtWidgets.QLabel(error_message)
        self.error_text.setWordWrap(True)
        self.error_text.setStyleSheet("color: #ff6b6b; font-size: 12pt; padding: 10px;")
        layout.addWidget(self.error_text)

        self.details_group: QtWidgets.QGroupBox | None = None
        self.details_text: QtWidgets.QTextEdit | None = None

        # Expandable technical details
        if technical_details or log_excerpt:
            self.details_group = QtWidgets.QGroupBox("Technical Details (Click to expand)")
            self.details_group.setCheckable(True)
            self.details_group.setChecked(False)
            self.details_group.setAccessibleName("Technical Details Collapsible Group")
            self.details_group.setToolTip("Click to expand or collapse technical error details and log output")
            self.details_group.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            details_layout = QtWidgets.QVBoxLayout(self.details_group)

            self.details_text = QtWidgets.QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setFontFamily("Courier New")
            self.details_text.setAccessibleName("Technical Error Details and Log Excerpt")

            full_details = ""
            if technical_details:
                full_details += f"Error Details:\n{technical_details}\n\n"
            if log_excerpt:
                full_details += f"Recent Log:\n{log_excerpt}"

            self.details_text.setPlainText(full_details)
            details_layout.addWidget(self.details_text)
            layout.addWidget(self.details_group)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.copy_btn = QtWidgets.QPushButton("Copy to Clipboard")
        self.copy_btn.setAccessibleName("Copy Error Details to Clipboard")
        self.copy_btn.setToolTip("Copy all error details to clipboard")
        self.copy_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(
                error_message, technical_details, log_excerpt
            )
        )
        button_layout.addWidget(self.copy_btn)

        self.report_btn = QtWidgets.QPushButton("Report Issue")
        self.report_btn.setAccessibleName("Report Issue on GitHub")
        self.report_btn.setToolTip("Open GitHub issues page to report this error")
        self.report_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.report_btn.clicked.connect(self._report_issue)
        button_layout.addWidget(self.report_btn)

        button_layout.addStretch()

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.setAccessibleName("Close Error Details Dialog")
        self.close_btn.setToolTip("Close error details dialog")
        self.close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _copy_to_clipboard(self, message: str, technical: str, log: str) -> None:
        """Copy all error details to clipboard with visual confirmation."""
        clipboard_text = f"""Error Message:
{message}

Technical Details:
{technical}

Recent Log:
{log}
"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(clipboard_text)
        logger.info("Error details copied to clipboard")

        target_btn = self.copy_btn
        try:
            original_text = target_btn.text()
            target_btn.setText("✓ Copied!")

            def _restore_text() -> None:
                try:
                    target_btn.setText(original_text)
                except RuntimeError:
                    pass

            QtCore.QTimer.singleShot(2000, self, _restore_text)
        except RuntimeError:
            pass

    def _report_issue(self) -> None:
        """Open GitHub issues page."""
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen" or os.environ.get("PYTEST_CURRENT_TEST"):
            logger.info("Headless test mode: skipping browser opening for issue reporting")
            return

        url = "https://github.com/cdgatenbee/valis-wsi/issues/new"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        logger.info("Opened GitHub issues page")


def show_error_dialog(
    parent: QtWidgets.QWidget,
    error_message: str,
    exception: Exception | None = None,
    log_file: Path | None = None,
) -> None:
    """
    Show an enhanced error dialog with technical details.

    Args:
        parent: Parent widget
        error_message: User-friendly error message
        exception: Optional exception object for technical details
        log_file: Optional path to log file for log excerpt
    """
    technical_details = ""
    if exception:
        import traceback

        technical_details = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

    log_excerpt = ""
    if log_file and log_file.exists():
        try:
            # Read last 50 lines of log file
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_excerpt = "".join(lines[-50:])
        except Exception:
            logger.exception("Failed to read log file")

    dialog = ErrorDetailDialog(error_message, technical_details, log_excerpt, parent)
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen" or os.environ.get("PYTEST_CURRENT_TEST"):
        return
    dialog.exec()
