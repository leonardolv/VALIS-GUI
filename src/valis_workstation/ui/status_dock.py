from __future__ import annotations

import logging

from PySide6 import QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon
from valis_workstation.utils.qt_logging import QtLogEmitter

logger = logging.getLogger(__name__)


class StatusDock(QtWidgets.QDockWidget):
    def __init__(
        self, emitter: QtLogEmitter, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__("Status", parent)
        self.setObjectName("StatusDock")
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)

        self._stage_label = QtWidgets.QLabel("Stage: Idle")

        self._log_header = QtWidgets.QLabel("Log Output")
        self._log_header.setProperty("role", "sidebar-header")

        log_controls = QtWidgets.QHBoxLayout()
        self._auto_scroll_check = QtWidgets.QCheckBox("Auto-scroll")
        self._auto_scroll_check.setChecked(True)
        self._clear_log_button = QtWidgets.QPushButton("Clear Log")
        self._clear_log_button.setIcon(
            load_icon(
                "trash", self, QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton
            )
        )
        self._clear_log_button.setProperty("panelAction", True)
        self._clear_log_button.clicked.connect(self._clear_log)

        self._copy_log_button = QtWidgets.QPushButton("Copy Log")
        self._copy_log_button.setIcon(
            load_icon(
                "copy", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self._copy_log_button.setProperty("panelAction", True)
        self._copy_log_button.clicked.connect(self._copy_log)

        log_controls.addWidget(self._auto_scroll_check)
        log_controls.addStretch()
        log_controls.addWidget(self._copy_log_button)
        log_controls.addWidget(self._clear_log_button)

        self._cancel_button = QtWidgets.QPushButton("Cancel Registration")
        self._cancel_button.setIcon(
            load_icon(
                "cancel", self, QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton
            )
        )
        self._cancel_button.setVisible(False)
        self._cancel_button.setToolTip("Cancel the currently running registration")

        self._log_console = QtWidgets.QTextEdit()
        self._log_console.setReadOnly(True)
        self._log_console.document().setMaximumBlockCount(2000)

        layout.addWidget(self._stage_label)
        layout.addWidget(self._progress)
        layout.addWidget(self._cancel_button)
        layout.addWidget(self._log_header)
        layout.addLayout(log_controls)
        layout.addWidget(self._log_console)
        self.setWidget(container)

        emitter.log_line.connect(self._append_log)

    def _append_log(self, line: str) -> None:
        self._log_console.append(line)
        if self._auto_scroll_check.isChecked():
            scroll = self._log_console.verticalScrollBar()
            scroll.setValue(scroll.maximum())

    def _clear_log(self) -> None:
        self._log_console.clear()

    def _copy_log(self) -> None:
        text = self._log_console.toPlainText()
        QtWidgets.QApplication.clipboard().setText(text)

    def set_progress(self, value: int) -> None:
        self._progress.setValue(value)
        if value == 0:
            self._stage_label.setText("Stage: Starting")
        elif value < 100:
            self._stage_label.setText("Stage: Running")
        else:
            self._stage_label.setText("Stage: Complete")
        if value == 100:
            logger.debug("Progress completed: 100%%")
        elif value % 25 == 0:
            logger.debug("Progress: %d%%", value)

    def show_cancel_button(self, show: bool) -> None:
        """Show or hide the cancel button."""
        self._cancel_button.setVisible(show)

    def connect_cancel(self, callback) -> None:
        """Connect cancel button to a callback."""
        try:
            self._cancel_button.clicked.disconnect()
        except Exception:
            pass
        self._cancel_button.clicked.connect(callback)
