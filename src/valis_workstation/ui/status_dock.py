from __future__ import annotations

from PySide6 import QtWidgets

from valis_workstation.utils.qt_logging import QtLogEmitter


class StatusDock(QtWidgets.QDockWidget):
    def __init__(self, emitter: QtLogEmitter, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Status", parent)
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)

        self._log_console = QtWidgets.QTextEdit()
        self._log_console.setReadOnly(True)

        layout.addWidget(self._progress)
        layout.addWidget(self._log_console)
        self.setWidget(container)

        emitter.log_line.connect(self._log_console.append)

    def set_progress(self, value: int) -> None:
        self._progress.setValue(value)
