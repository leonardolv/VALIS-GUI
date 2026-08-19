from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from valis_workstation.main_window import MainWindow
from valis_workstation.ui.dialogs.first_run_wizard import FirstRunWizard
from valis_workstation.ui.splash_screen import SplashScreen
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


class _ToolTipSuppressionFilter(QtCore.QObject):
    """Blocks every tooltip while ``ui/show_tooltips`` is off.

    The Preferences dialog's "Show tooltips" checkbox persisted this setting
    and nothing ever read it back — no single call site owns "did a tooltip
    fire", since tooltips come from dozens of individual widgets via Qt's own
    hover machinery, not from app code. Installed application-wide, this is
    the one place that can intercept them all: ``QEvent.Type.ToolTip`` is
    delivered to the widget under the cursor before Qt paints the tooltip,
    and returning ``True`` here consumes the event so it never does. The
    setting is re-read on every tooltip rather than cached, so a change in
    Preferences takes effect immediately without restarting the app.
    """

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.ToolTip:
            settings = QtCore.QSettings("VALIS", "Workstation")
            if not settings.value("ui/show_tooltips", True, type=bool):
                return True
        return super().eventFilter(obj, event)


def _install_excepthook(app: QtWidgets.QApplication) -> None:
    def _hook(exc_type, exc_value, traceback_obj):
        logger.exception(
            "Unhandled exception", exc_info=(exc_type, exc_value, traceback_obj)
        )
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

    # Kept alive as an attribute, not just installed: PySide does not treat
    # installEventFilter as taking ownership, so a filter with no surviving
    # Python reference can be garbage-collected out from under the app.
    app._tooltip_suppression_filter = _ToolTipSuppressionFilter(app)
    app.installEventFilter(app._tooltip_suppression_filter)

    stylesheet = _load_stylesheet(repo_root)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # ── Show splash screen while heavy subsystems load ───────────
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    splash.set_status("Starting Java Virtual Machine…")
    jvm_started = _start_jvm()

    splash.set_status("Checking SimpleElastix…")
    simple_elastix_available = _simple_elastix_available()

    splash.set_status("Building user interface…")
    main_window = MainWindow(repo_root, log_emitter, simple_elastix_available)

    settings = QtCore.QSettings("VALIS", "Workstation")
    first_run_done = settings.value("first_run_completed", False, type=bool)
    if not first_run_done:
        splash.set_status("Running first-time setup…")
        wizard = FirstRunWizard(main_window)
        if wizard.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            cfg = main_window._properties_dock.config()
            cfg.project_name = wizard.selected_project_name()
            main_window._properties_dock.set_config(cfg)
            main_window._properties_dock.apply_output_profile(
                wizard.selected_output_profile()
            )
            settings.setValue("first_run_completed", True)

    splash.set_status("Ready")

    def _cleanup() -> None:
        if jvm_started:
            _shutdown_jvm()

    app.aboutToQuit.connect(_cleanup)

    # Fade out splash and show main window
    splash.finish(main_window)

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
