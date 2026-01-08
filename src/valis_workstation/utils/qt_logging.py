from __future__ import annotations

import logging
from PySide6 import QtCore


class QtLogEmitter(QtCore.QObject):
    log_line = QtCore.Signal(str)


class QtSignalHandler(logging.Handler):
    def __init__(self, emitter: QtLogEmitter) -> None:
        super().__init__()
        self._emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self._emitter.log_line.emit(message)
