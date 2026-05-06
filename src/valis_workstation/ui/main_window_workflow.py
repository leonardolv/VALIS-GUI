from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from valis_workstation.models.config import Config
from valis_workstation.ui.dialogs.error_detail_dialog import show_error_dialog
from valis_workstation.utils.validation import validate_slides
from valis_workstation.workers.valis_worker import ValisWorker

if TYPE_CHECKING:
    from valis_workstation.main_window import MainWindow

logger = logging.getLogger(__name__)


def start_registration(window: MainWindow) -> None:
    slides = window._project_dock.slides()
    if not slides:
        QtWidgets.QMessageBox.warning(window, "VALIS", "No slides to register.")
        return

    config = window._properties_dock.config()
    output_dir = window._repo_root / "output" / config.project_name

    validation = validate_slides(slides, output_dir)

    if validation.has_errors():
        error_msg = (
            "Cannot start registration due to the following errors:\n\n"
            + "\n".join(f"- {err}" for err in validation.errors)
        )
        QtWidgets.QMessageBox.critical(window, "Validation Failed", error_msg)
        logger.error(
            "Pre-registration validation failed: %s", "; ".join(validation.errors)
        )
        return

    if validation.has_warnings():
        warning_msg = "The following warnings were detected:\n\n" + "\n".join(
            f"- {warning}" for warning in validation.warnings
        )
        warning_msg += "\n\nDo you want to proceed anyway?"

        reply = QtWidgets.QMessageBox.question(
            window,
            "Validation Warnings",
            warning_msg,
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            logger.info("Registration cancelled due to validation warnings")
            return

    if not confirm_registration(window, slides, output_dir):
        logger.info("Registration cancelled by user")
        return

    context = {
        "slides": slides,
        "config": config,
        "output_dir": output_dir,
    }
    window._last_run_context = context
    start_registration_from_context(window, context)


def start_registration_from_context(window: MainWindow, context: dict) -> None:
    """Start worker from a stored run context (new run or resume)."""
    slides: list[Path] = context["slides"]
    config: Config = context["config"]
    output_dir: Path = context["output_dir"]

    window._status_bar.showMessage(f"Starting registration of {len(slides)} slides...")
    window._set_workflow_step("Register")
    window._set_registration_running(True)
    if hasattr(window, "_open_output_folder_link"):
        window._open_output_folder_link.setVisible(False)
    logger.info("Starting registration with %d slides", len(slides))

    window._worker_thread = QtCore.QThread(window)
    window._worker = ValisWorker(config, slides, output_dir)
    window._worker.moveToThread(window._worker_thread)

    window._worker_thread.started.connect(window._worker.run)
    window._worker.started.connect(lambda: window._status_dock.set_progress(0))
    window._worker.started.connect(lambda: window._status_dock.set_stage("Starting"))
    window._worker.started.connect(lambda: window._status_dock.show_cancel_button(True))
    window._worker.progress.connect(window._status_dock.set_progress)
    window._worker.stage_changed.connect(window._status_dock.set_stage)
    window._worker.finished.connect(window._on_worker_finished)
    window._worker.failed.connect(window._on_worker_failed)
    window._worker.cancelled.connect(window._on_worker_cancelled)
    window._worker.finished.connect(window._worker_thread.quit)
    window._worker.failed.connect(window._worker_thread.quit)
    window._worker.cancelled.connect(window._worker_thread.quit)
    window._worker_thread.finished.connect(window._cleanup_worker)

    window._status_dock.connect_cancel(window._request_cancellation)

    window._worker_thread.start()


def resume_last_registration(window: MainWindow) -> None:
    """Resume/re-run the last registration context after cancel/failure."""
    if not window._last_run_context:
        QtWidgets.QMessageBox.information(
            window, "Resume", "No previous registration context available."
        )
        return
    if window._worker_thread and window._worker_thread.isRunning():
        QtWidgets.QMessageBox.information(
            window, "Resume", "Registration is already running."
        )
        return
    window._status_bar.showMessage("Resuming last registration...", 3000)
    start_registration_from_context(window, window._last_run_context)


def cleanup_worker(window: MainWindow) -> None:
    window._status_dock.show_cancel_button(False)
    window._set_registration_running(False)
    window._worker_thread = None
    window._worker = None


def request_cancellation(window: MainWindow) -> None:
    """Handle user request to cancel registration."""
    if not window._worker:
        return

    reply = QtWidgets.QMessageBox.question(
        window,
        "Cancel Registration",
        "Are you sure you want to cancel the registration?\n"
        "Slides processed so far will remain in the output folder. "
        "Pending slides will not be registered.",
        QtWidgets.QMessageBox.StandardButton.Yes
        | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.No,
    )

    if reply == QtWidgets.QMessageBox.StandardButton.Yes:
        logger.info("User requested cancellation")
        window._worker.cancel()
        window._status_bar.showMessage("Canceling registration...")


def on_worker_cancelled(window: MainWindow) -> None:
    """Handle worker cancellation."""
    logger.info("Registration cancelled")
    window._status_dock.reset_progress()
    window._status_dock.set_stage("Cancelled")
    window._set_workflow_step("Configure")
    window._status_bar.showMessage("Registration cancelled", 5000)
    QtWidgets.QMessageBox.information(
        window,
        "VALIS",
        "Registration was cancelled.\n"
        "Slides processed so far remain in the output folder.",
    )


def confirm_registration(window: MainWindow, slides: list[Path], output_dir: Path) -> bool:
    """Show one confirmation dialog with estimates and settings."""
    config = window._properties_dock.config()

    total_size_bytes, has_missing = safe_total_size_bytes(slides)
    total_size_gb = total_size_bytes / (1024**3)
    est_output_gb = max(0.5, total_size_gb * 2.5)

    est_minutes = len(slides) * (1.6 if config.non_rigid_registration else 0.8)
    if config.non_rigid_registration:
        est_minutes *= 1.1
    if config.micro_registration:
        est_minutes *= 1.8
    if config.max_image_size > 4096:
        est_minutes *= 1.5
    if config.use_masks:
        est_minutes *= 1.2
    if config.use_gpu:
        est_minutes *= 0.7
    est_minutes = max(1, int(est_minutes))

    warning_html = ""
    if has_missing:
        warning_html = (
            '<p style="color:#E49B0F; margin: 2px 0;"><b>Warning:</b> '
            "Input size calculation incomplete.</p>"
        )

    msg = QtWidgets.QMessageBox(window)
    msg.setWindowTitle("Confirm Registration")
    msg.setIcon(QtWidgets.QMessageBox.Icon.Question)

    text = f"""<h3>Ready to Register {len(slides)} Slide{"s" if len(slides) != 1 else ""}</h3>
<table style="margin: 6px 0;">
    <tr><td><b>Input size:</b></td><td>{total_size_gb:.2f} GB</td></tr>
    <tr><td><b>Estimated output:</b></td><td>~{est_output_gb:.2f} GB</td></tr>
    <tr><td><b>Estimated time:</b></td><td>~{est_minutes} min</td></tr>
    <tr><td><b>Output dir:</b></td><td>{output_dir}</td></tr>
<tr><td><b>Project:</b></td><td>{config.project_name}</td></tr>
</table>
{warning_html}
<p><b>Registration settings</b></p>
<table style="margin: 4px 0;">
<tr><td>Rigid registration:</td><td>{"Yes" if config.rigid_registration else "No"}</td></tr>
<tr><td>Non-rigid registration:</td><td>{"Yes" if config.non_rigid_registration else "No"}</td></tr>
<tr><td>Max image size:</td><td>{config.max_image_size} px</td></tr>
<tr><td>Feature detector:</td><td>{config.feature_detector}</td></tr>
<tr><td>Rigid transform:</td><td>{config.transformer_type}</td></tr>
<tr><td>Reference slide:</td><td>{config.reference_slide or "Auto-detect"}</td></tr>
<tr><td>Crop mode:</td><td>{config.crop_mode}</td></tr>
<tr><td>Tissue masks:</td><td>{"Yes" if config.use_masks else "No"}</td></tr>
<tr><td>Denoise:</td><td>{"Yes" if config.denoise else "No"}</td></tr>
<tr><td>Slides pre-ordered:</td><td>{"Yes" if config.imgs_ordered else "No (auto-sort)"}</td></tr>
<tr><td>Micro-registration:</td><td>{"Yes (" + str(config.micro_max_image_size) + " px)" if config.micro_registration else "No"}</td></tr>
<tr><td>GPU:</td><td>{"Yes" if config.use_gpu else "No"}</td></tr>
</table>
<p><b>Output settings</b></p>
<table style="margin: 4px 0;">
<tr><td>Compression:</td><td>{config.compression_level}</td></tr>
<tr><td>Pyramid levels:</td><td>{config.pyramid_levels}</td></tr>
<tr><td>Tile size:</td><td>{config.tile_size} px</td></tr>
<tr><td>JPEG quality:</td><td>{config.image_quality}%</td></tr>
</table>
<p>Proceed?</p>"""

    msg.setText(text)
    msg.setStandardButtons(
        QtWidgets.QMessageBox.StandardButton.Yes
        | QtWidgets.QMessageBox.StandardButton.No
    )
    msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)

    return msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes


def safe_total_size_bytes(slides: list[Path]) -> tuple[int, bool]:
    total = 0
    has_missing = False
    for slide in slides:
        try:
            if slide.exists():
                total += slide.stat().st_size
            else:
                has_missing = True
        except OSError:
            has_missing = True
            continue
    return total, has_missing


def on_worker_finished(window: MainWindow, result: dict) -> None:
    logger.info("Registration completed")
    window._status_dock.set_progress(100)
    window._status_dock.set_stage("Complete")
    window._last_result = result
    window._update_tools_enabled()
    window._set_workflow_step("Review")
    window._load_registered_layers(result)
    window._status_bar.showMessage("Registration completed successfully", 5000)
    if hasattr(window, "_open_output_folder_link"):
        window._open_output_folder_link.setVisible(True)
    QtWidgets.QMessageBox.information(window, "VALIS", "Registration complete.")


def on_worker_failed(window: MainWindow, message: str, technical_details: str = "") -> None:
    logger.error("Registration failed: %s", message)
    window._status_dock.set_stage("Failed")
    window._set_workflow_step("Configure")
    window._status_bar.showMessage("Registration failed", 5000)

    log_file = window._repo_root / "logs" / "valis_workstation.log"

    show_error_dialog(
        window,
        f"Registration failed: {message}",
        technical_details=technical_details,
        log_file=log_file if log_file.exists() else None,
    )
