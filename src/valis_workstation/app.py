from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from valis_workstation.main_window import MainWindow
from valis_workstation.utils.logging_config import setup_logging
from valis_workstation.utils.qt_logging import QtLogEmitter, QtSignalHandler

logger = logging.getLogger(__name__)


def _load_stylesheet(repo_root: Path) -> str:
    qss_path = repo_root / "src" / "valis_workstation" / "styles" / "adobe_dark.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


def _simple_elastix_available() -> bool:
    if importlib.util.find_spec("SimpleITK") is None:
        return False
    simpleitk = importlib.import_module("SimpleITK")
    return hasattr(simpleitk, "ElastixImageFilter")


def _start_jvm() -> bool:
    if importlib.util.find_spec("scyjava") is None:
        logger.warning("scyjava not available; JVM will not start.")
        return False
    scyjava = importlib.import_module("scyjava")
    try:
        scyjava.start_jvm()
        logger.info("JVM started")
        return True
    except Exception:
        logger.exception("Failed to start JVM")
        return False


def _shutdown_jvm() -> None:
    if importlib.util.find_spec("scyjava") is None:
        return
    scyjava = importlib.import_module("scyjava")
    try:
        scyjava.shutdown_jvm()
        logger.info("JVM shutdown")
    except Exception:
        logger.exception("Failed to shutdown JVM")


def _install_excepthook(app: QtWidgets.QApplication) -> None:
    def _hook(exc_type, exc_value, traceback_obj):
        logger.exception("Unhandled exception", exc_info=(exc_type, exc_value, traceback_obj))
        QtWidgets.QMessageBox.critical(
            None,
            "VALIS Workstation",
            "An unexpected error occurred. Please check the logs for details.",
        )
        app.quit()

    sys.excepthook = _hook


def run_app(repo_root: Path) -> int:
    log_dir = repo_root / "logs"
    setup_logging(log_dir)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("VALIS Workstation")

    log_emitter = QtLogEmitter()
    qt_handler = QtSignalHandler(log_emitter)
    qt_handler.setLevel(logging.INFO)
    qt_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logging.getLogger().addHandler(qt_handler)

    _install_excepthook(app)

    stylesheet = _load_stylesheet(repo_root)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    jvm_started = _start_jvm()

    simple_elastix_available = _simple_elastix_available()

    main_window = MainWindow(repo_root, log_emitter, simple_elastix_available)
    main_window.show()

    def _cleanup() -> None:
        if jvm_started:
            _shutdown_jvm()

    app.aboutToQuit.connect(_cleanup)

    try:
        return app.exec()
    except Exception:
        logger.exception("Application crashed")
        QtWidgets.QMessageBox.critical(
            None,
            "VALIS Workstation",
            "The application encountered an unexpected error. See logs for details.",
        )
        return 1
