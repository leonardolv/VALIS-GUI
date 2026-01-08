from __future__ import annotations

import logging
from pathlib import Path

from PySide6 import QtCore

from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import run_valis_pipeline

logger = logging.getLogger(__name__)


class ValisWorker(QtCore.QObject):
    started = QtCore.Signal()
    progress = QtCore.Signal(int)
    finished = QtCore.Signal(dict)
    failed = QtCore.Signal(str)

    def __init__(self, config: Config, slides: list[Path], output_dir: Path) -> None:
        super().__init__()
        self._config = config
        self._slides = slides
        self._output_dir = output_dir

    @QtCore.Slot()
    def run(self) -> None:
        self.started.emit()
        try:
            result = run_valis_pipeline(
                self._config,
                self._slides,
                self._output_dir,
                progress_callback=self.progress.emit,
            )
        except Exception as exc:
            logger.exception("VALIS pipeline failed")
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)
