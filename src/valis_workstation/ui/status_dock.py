from __future__ import annotations

import logging
from PySide6 import QtWidgets

from valis_workstation.utils.qt_logging import QtLogEmitter

logger = logging.getLogger(__name__)


class StatusDock(QtWidgets.QDockWidget):
    def __init__(self, emitter: QtLogEmitter, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Status", parent)
        self.setObjectName("StatusDock")
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        
        self._cancel_button = QtWidgets.QPushButton("Cancel Registration")
        self._cancel_button.setVisible(False)
        self._cancel_button.setToolTip("Cancel the currently running registration")

        self._log_console = QtWidgets.QTextEdit()
        self._log_console.setReadOnly(True)

        layout.addWidget(self._progress)
        layout.addWidget(self._cancel_button)
        layout.addWidget(self._log_console)
        self.setWidget(container)

        emitter.log_line.connect(self._log_console.append)

    def set_progress(self, value: int) -> None:
        self._progress.setValue(value)
        if value == 100:
            logger.debug("Progress completed: 100%%")
        elif value % 25 == 0:
            logger.debug("Progress: %d%%", value)

    def show_cancel_button(self, show: bool) -> None:
        """Show or hide the cancel button."""
        self._cancel_button.setVisible(show)

    def connect_cancel(self, callback) -> None:
        """Connect cancel button to a callback."""
        self._cancel_button.clicked.connect(callback)
