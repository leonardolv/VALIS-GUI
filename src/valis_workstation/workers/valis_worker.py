from __future__ import annotations

import logging
import time
from pathlib import Path

from PySide6 import QtCore

from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import run_valis_pipeline
from valis_workstation.utils.performance import get_performance_monitor

logger = logging.getLogger(__name__)


class ValisWorker(QtCore.QObject):
    started = QtCore.Signal()
    progress = QtCore.Signal(int)
    finished = QtCore.Signal(dict)
    failed = QtCore.Signal(str)
    cancelled = QtCore.Signal()

    def __init__(self, config: Config, slides: list[Path], output_dir: Path) -> None:
        super().__init__()
        self._config = config
        self._slides = slides
        self._output_dir = output_dir
        self._cancel_requested = False

    def cancel(self) -> None:
        """Request cancellation of the registration."""
        logger.info("Cancellation requested")
        self._cancel_requested = True

    @QtCore.Slot()
    def run(self) -> None:
        self.started.emit()
        started_at = time.time()
        try:
            result = run_valis_pipeline(
                self._config,
                self._slides,
                self._output_dir,
                progress_callback=self.progress.emit,
                cancel_check=lambda: self._cancel_requested,
            )

            if self._cancel_requested:
                logger.info("Registration cancelled")
                self.cancelled.emit()
                return

        except Exception as exc:
            logger.exception("VALIS pipeline failed")
            self.failed.emit(str(exc))
            return
        get_performance_monitor().track_registration(time.time() - started_at)
        self.finished.emit(result)
