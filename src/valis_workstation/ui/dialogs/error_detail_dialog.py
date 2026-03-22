"""Enhanced error dialog with detailed information and copy-to-clipboard functionality."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6 import QtCore, QtWidgets

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
        message_label = QtWidgets.QLabel("<h3>An error occurred:</h3>")
        layout.addWidget(message_label)

        error_text = QtWidgets.QLabel(error_message)
        error_text.setWordWrap(True)
        error_text.setStyleSheet("color: #ff6b6b; font-size: 12pt; padding: 10px;")
        layout.addWidget(error_text)

        # Expandable technical details
        if technical_details or log_excerpt:
            details_group = QtWidgets.QGroupBox("Technical Details (Click to expand)")
            details_group.setCheckable(True)
            details_group.setChecked(False)
            details_layout = QtWidgets.QVBoxLayout(details_group)

            details_text = QtWidgets.QTextEdit()
            details_text.setReadOnly(True)
            details_text.setFontFamily("Courier New")

            full_details = ""
            if technical_details:
                full_details += f"Error Details:\n{technical_details}\n\n"
            if log_excerpt:
                full_details += f"Recent Log:\n{log_excerpt}"

            details_text.setPlainText(full_details)
            details_layout.addWidget(details_text)
            layout.addWidget(details_group)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        copy_button = QtWidgets.QPushButton("Copy to Clipboard")
        copy_button.setToolTip("Copy all error details to clipboard")
        copy_button.clicked.connect(
            lambda: self._copy_to_clipboard(
                error_message, technical_details, log_excerpt
            )
        )
        button_layout.addWidget(copy_button)

        report_button = QtWidgets.QPushButton("Report Issue")
        report_button.setToolTip("Open GitHub issues page to report this error")
        report_button.clicked.connect(self._report_issue)
        button_layout.addWidget(report_button)

        button_layout.addStretch()

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _copy_to_clipboard(self, message: str, technical: str, log: str) -> None:
        """Copy all error details to clipboard."""
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

        # Show brief confirmation
        sender = self.sender()
        if isinstance(sender, QtWidgets.QPushButton):
            original_text = sender.text()
            sender.setText("✓ Copied!")
            QtCore.QTimer.singleShot(2000, lambda: sender.setText(original_text))

    def _report_issue(self) -> None:
        """Open GitHub issues page."""
        from PySide6 import QtGui

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
    dialog.exec()
