from __future__ import annotations

import logging
import threading
import traceback
from pathlib import Path

from PySide6 import QtCore

from valis_workstation.models.config import Config
from valis_workstation.services.valis_pipeline import run_valis_pipeline

logger = logging.getLogger(__name__)


class ValisWorker(QtCore.QObject):
    started = QtCore.Signal()
    progress = QtCore.Signal(int)
    stage_changed = QtCore.Signal(str)
    finished = QtCore.Signal(dict)
    failed = QtCore.Signal(str, str)
    cancelled = QtCore.Signal()

    def __init__(self, config: Config, slides: list[Path], output_dir: Path) -> None:
        super().__init__()
        self._config = config
        self._slides = slides
        self._output_dir = output_dir
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request cancellation of the registration (thread-safe)."""
        logger.info("Cancellation requested")
        self._cancel_event.set()

    @QtCore.Slot()
    def run(self) -> None:
        self.started.emit()
        self.stage_changed.emit("Starting")
        try:
            result = run_valis_pipeline(
                self._config,
                self._slides,
                self._output_dir,
                progress_callback=self.progress.emit,
                stage_callback=self.stage_changed.emit,
                cancel_check=self._cancel_event.is_set,
            )

            if self._cancel_event.is_set():
                logger.info("Registration cancelled")
                self.stage_changed.emit("Cancelled")
                self.cancelled.emit()
                return

        except Exception as exc:
            logger.exception("VALIS pipeline failed")
            self.stage_changed.emit("Failed")
            self.failed.emit(str(exc), traceback.format_exc())
            return
        self.stage_changed.emit("Complete")
        self.finished.emit(result)
