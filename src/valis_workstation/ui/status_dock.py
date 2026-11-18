from __future__ import annotations

import logging
import os
import re
import time

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon
from valis_workstation.utils.qt_logging import QtLogEmitter

logger = logging.getLogger(__name__)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _is_headless() -> bool:
    """Return True if running in offscreen or automated test environment."""
    return (
        os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        or "PYTEST_CURRENT_TEST" in os.environ
        or os.environ.get("HEADLESS") == "1"
    )


class StatusDock(QtWidgets.QDockWidget):
    def __init__(
        self, emitter: QtLogEmitter, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__("Status", parent)
        self.setObjectName("StatusDock")
        self.setAccessibleName("Pipeline Status and Log Dock")
        self.setAccessibleDescription(
            "Displays registration pipeline progress, stage timing, and live log console."
        )
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._progress = QtWidgets.QProgressBar()
        self._progress.setObjectName("statusProgressBar")
        self._progress.setAccessibleName("Pipeline Progress")
        self._progress.setAccessibleDescription("Progress percentage of the current registration pipeline.")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFormat("%p%")

        self._stage_label = QtWidgets.QLabel("Stage: Idle")
        self._stage_label.setObjectName("statusStageLabel")
        self._stage_label.setAccessibleName("Pipeline Stage")
        self._stage_label.setToolTip("Current pipeline stage")
        self._timing_label = QtWidgets.QLabel("Elapsed: 00:00:00 | ETA: --:--:--")
        self._timing_label.setObjectName("statusTimingLabel")
        self._timing_label.setAccessibleName("Stage Timing and ETA")
        self._timing_label.setProperty("role", "sidebar-subtle")
        self._timing_label.setToolTip("Elapsed time since run started and estimated time remaining")
        self._run_started_at: float | None = None
        self._last_progress_value = 0

        self._timing_timer = QtCore.QTimer(self)
        self._timing_timer.setInterval(1000)
        self._timing_timer.timeout.connect(self._update_timing)
        self._timing_timer.start()

        self._log_header = QtWidgets.QLabel("Log Output")
        self._log_header.setObjectName("statusLogHeader")
        self._log_header.setAccessibleName("Log Output Header")
        self._log_header.setProperty("role", "sidebar-header")

        filter_row = QtWidgets.QHBoxLayout()
        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setObjectName("statusLogFilterEdit")
        self._filter_edit.setAccessibleName("Filter Log Lines")
        self._filter_edit.setAccessibleDescription("Case-insensitive keyword filter for log messages.")
        self._filter_edit.setPlaceholderText("Filter log lines...")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.setToolTip("Filter log lines by keyword (case-insensitive)")
        self._filter_edit.textChanged.connect(self._rebuild_log_view)
        filter_row.addWidget(self._filter_edit, 1)

        # Filter + log actions share ONE row: stacked in separate rows
        # they overlapped each other when the bottom panel was short.
        log_controls = filter_row
        self._auto_scroll_check = QtWidgets.QCheckBox("Auto-scroll")
        self._auto_scroll_check.setObjectName("statusAutoScrollCheck")
        self._auto_scroll_check.setAccessibleName("Auto-scroll Log")
        self._auto_scroll_check.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._auto_scroll_check.setChecked(True)
        self._auto_scroll_check.setToolTip(
            "Automatically scroll the log to show new lines as they arrive"
        )

        self._clear_log_button = QtWidgets.QPushButton("Clear Log")
        self._clear_log_button.setObjectName("statusClearLogBtn")
        self._clear_log_button.setAccessibleName("Clear Log")
        self._clear_log_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._clear_log_button.setIcon(
            load_icon(
                "trash", self, QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton
            )
        )
        self._clear_log_button.setProperty("panelAction", True)
        self._clear_log_button.setEnabled(False)
        self._clear_log_button.setToolTip("Clear the log display. The log file on disk is not affected.")
        self._clear_log_button.clicked.connect(self._clear_log)

        self._copy_log_button = QtWidgets.QPushButton("Copy Log")
        self._copy_log_button.setObjectName("statusCopyLogBtn")
        self._copy_log_button.setAccessibleName("Copy Log")
        self._copy_log_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._copy_log_button.setIcon(
            load_icon(
                "copy", self, QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self._copy_log_button.setProperty("panelAction", True)
        self._copy_log_button.setEnabled(False)
        self._copy_log_button.setToolTip("Copy all log lines to clipboard")
        self._copy_log_button.clicked.connect(self._copy_log)

        log_controls.addWidget(self._auto_scroll_check)
        log_controls.addWidget(self._copy_log_button)
        log_controls.addWidget(self._clear_log_button)

        self._cancel_button = QtWidgets.QPushButton("Cancel Registration")
        self._cancel_button.setObjectName("statusCancelBtn")
        self._cancel_button.setAccessibleName("Cancel Registration")
        self._cancel_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._cancel_button.setIcon(
            load_icon(
                "cancel", self, QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton
            )
        )
        self._cancel_button.setVisible(False)
        self._cancel_button.setToolTip("Cancel the currently running registration")

        self._log_console = QtWidgets.QTextEdit()
        self._log_console.setObjectName("statusLogConsole")
        self._log_console.setReadOnly(True)
        self._log_console.setAccessibleName("Registration Log Console")
        self._log_console.setAccessibleDescription("Console view of timestamped registration logs and diagnostics.")
        self._log_console.document().setMaximumBlockCount(2000)
        self._log_console.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._log_console.customContextMenuRequested.connect(self._show_log_context_menu)
        self._log_lines: list[str] = []

        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        divider.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

        status_row = QtWidgets.QHBoxLayout()
        status_row.addWidget(self._stage_label)
        status_row.addStretch(1)
        status_row.addWidget(self._timing_label)

        layout.addLayout(status_row)
        layout.addWidget(self._progress)
        layout.addWidget(self._cancel_button)
        layout.addWidget(divider)
        layout.addWidget(self._log_header)
        layout.addLayout(filter_row)
        layout.addWidget(self._log_console, 1)
        self.setWidget(container)

        emitter.log_line.connect(self._append_log)

    def _append_log(self, line: str) -> None:
        clean = _ANSI_RE.sub("", line).rstrip("\n")
        if not clean:
            return
        self._log_lines.append(clean)

        self._clear_log_button.setEnabled(True)
        self._copy_log_button.setEnabled(True)

        if self._filter_edit.text().strip():
            self._rebuild_log_view()
            return

        scroll = self._log_console.verticalScrollBar()
        at_bottom = scroll.value() >= max(0, scroll.maximum() - 2)
        self._log_console.append(clean)
        if self._auto_scroll_check.isChecked() and at_bottom:
            self._log_console.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def _rebuild_log_view(self) -> None:
        needle = self._filter_edit.text().strip().lower()
        scroll = self._log_console.verticalScrollBar()
        at_bottom = scroll.value() >= max(0, scroll.maximum() - 2)

        self._log_console.setUpdatesEnabled(False)
        self._log_console.clear()
        if not needle:
            for line in self._log_lines:
                self._log_console.append(line)
        else:
            for line in self._log_lines:
                if needle in line.lower():
                    self._log_console.append(line)
        self._log_console.setUpdatesEnabled(True)

        if self._auto_scroll_check.isChecked() and at_bottom:
            self._log_console.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def _show_log_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self._log_console)
        copy_selected = menu.addAction("Copy Selected")
        copy_all = menu.addAction("Copy All")
        save_as = menu.addAction("Save Log As...")

        action = menu.exec(self._log_console.mapToGlobal(pos))
        if action == copy_selected:
            selected = self._log_console.textCursor().selectedText()
            if selected:
                QtWidgets.QApplication.clipboard().setText(selected)
        elif action == copy_all:
            self._copy_log()
        elif action == save_as:
            self._save_log_as()

    def _clear_log(self, force: bool = False) -> None:
        if len(self._log_lines) > 0 and not force and not _is_headless():
            reply = QtWidgets.QMessageBox.question(
                self,
                "Clear Log",
                "Clear the log display? This cannot be undone.",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        self._log_lines.clear()
        self._log_console.clear()
        self._clear_log_button.setEnabled(False)
        self._copy_log_button.setEnabled(False)

    def _show_status_message(self, message: str, timeout: int = 3000) -> None:
        win = self.window() if callable(getattr(self, "window", None)) else None
        if win and hasattr(win, "statusBar") and callable(win.statusBar):
            sb = win.statusBar()
            if sb and hasattr(sb, "showMessage"):
                sb.showMessage(message, timeout)

    def _copy_log(self) -> None:
        text = "\n".join(self._log_lines)
        QtWidgets.QApplication.clipboard().setText(text)
        self._show_status_message("Log copied to clipboard", 3000)

    def _save_log_as(self, target_path: str | None = None) -> bool:
        out_path = target_path
        if not out_path:
            if _is_headless():
                self._show_status_message("Log save skipped in headless mode", 2000)
                return True
            settings = QtCore.QSettings("VALIS", "Workstation")
            last_dir = settings.value("ui/last_log_save_dir", str(__import__('pathlib').Path.home()))

            out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Log",
                last_dir + "/registration_log.txt",
                "Text Files (*.txt)",
            )
            if not out_path:
                return False
        try:
            settings = QtCore.QSettings("VALIS", "Workstation")
            settings.setValue("ui/last_log_save_dir", str(__import__('pathlib').Path(out_path).parent))
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(self._log_lines))
            self._show_status_message(f"Log saved to {out_path}", 4000)
            return True
        except Exception as exc:
            logger.exception("Failed to save log output: %s", exc)
            return False

    # -------------------------------------------------------------------------
    # Public widget property accessors
    # -------------------------------------------------------------------------

    @property
    def progress_bar(self) -> QtWidgets.QProgressBar:
        return self._progress

    @property
    def stage_label(self) -> QtWidgets.QLabel:
        return self._stage_label

    @property
    def timing_label(self) -> QtWidgets.QLabel:
        return self._timing_label

    @property
    def filter_edit(self) -> QtWidgets.QLineEdit:
        return self._filter_edit

    @property
    def auto_scroll_checkbox(self) -> QtWidgets.QCheckBox:
        return self._auto_scroll_check

    @property
    def clear_button(self) -> QtWidgets.QPushButton:
        return self._clear_log_button

    @property
    def copy_button(self) -> QtWidgets.QPushButton:
        return self._copy_log_button

    @property
    def cancel_button(self) -> QtWidgets.QPushButton:
        return self._cancel_button

    @property
    def log_console(self) -> QtWidgets.QTextEdit:
        return self._log_console

    # -------------------------------------------------------------------------
    # Ergonomic state queries and setters
    # -------------------------------------------------------------------------

    def progress_value(self) -> int:
        """Return the current progress percentage (0-100)."""
        return self._progress.value()

    def stage_text(self) -> str:
        """Return the current stage text (without 'Stage: ' prefix if present)."""
        text = self._stage_label.text()
        return text[len("Stage: "):] if text.startswith("Stage: ") else text

    def timing_text(self) -> str:
        """Return the current timing readout text."""
        return self._timing_label.text()

    def log_line_count(self) -> int:
        """Return the number of stored log lines."""
        return len(self._log_lines)

    def log_lines(self) -> list[str]:
        """Return a copy of the stored log lines."""
        return list(self._log_lines)

    def log_text(self) -> str:
        """Return all log lines concatenated with newlines."""
        return "\n".join(self._log_lines)

    def console_text(self) -> str:
        """Return the current visible text in the log console."""
        return self._log_console.toPlainText()

    def filter_text(self) -> str:
        """Return the current filter query string."""
        return self._filter_edit.text()

    def set_filter_text(self, text: str) -> None:
        """Set the log filter text."""
        self._filter_edit.setText(text)

    def is_auto_scroll_enabled(self) -> bool:
        """Return whether auto-scrolling is enabled."""
        return self._auto_scroll_check.isChecked()

    def set_auto_scroll_enabled(self, enabled: bool) -> None:
        """Set auto-scrolling enabled or disabled."""
        self._auto_scroll_check.setChecked(enabled)

    def is_cancel_visible(self) -> bool:
        """Return whether the cancel button is visible."""
        return not self._cancel_button.isHidden()

    def append_log_line(self, line: str) -> None:
        """Append a single log line."""
        self._append_log(line)

    # -------------------------------------------------------------------------
    # Programmatic action triggers
    # -------------------------------------------------------------------------

    def trigger_clear_log(self, force: bool = False) -> None:
        """Programmatically trigger clear log action."""
        self._clear_log(force=force)

    def trigger_copy_log(self) -> None:
        """Programmatically trigger copy log action."""
        self._copy_log()

    def trigger_cancel(self) -> None:
        """Programmatically trigger cancel registration button."""
        self._cancel_button.click()

    def set_stage(self, stage: str) -> None:
        self._stage_label.setText(f"Stage: {stage}")
        if stage.lower() in {"starting", "preparing pipeline"}:
            self._run_started_at = time.time()

    def set_progress(self, value: int) -> None:
        value = max(0, min(100, value))
        self._last_progress_value = value
        self._progress.setValue(value)
        if value >= 100:
            # Stop the 1 s timer from overwriting the final label with a
            # forever-growing elapsed time.
            self._run_started_at = None
            self._timing_label.setText("Elapsed: complete | ETA: 00:00:00")
        if value == 100:
            logger.debug("Progress completed: 100%%")
        elif value % 25 == 0:
            logger.debug("Progress: %d%%", value)

    def reset_progress(self) -> None:
        self._progress.setValue(0)
        self._last_progress_value = 0
        self._run_started_at = None
        self._timing_label.setText("Elapsed: 00:00:00 | ETA: --:--:--")

    def _update_timing(self) -> None:
        if self._run_started_at is None:
            return

        elapsed_s = int(max(0, time.time() - self._run_started_at))
        elapsed_txt = self._format_hms(elapsed_s)

        eta_txt = "--:--:--"
        if 0 < self._last_progress_value < 100:
            rate = self._last_progress_value / max(1.0, time.time() - self._run_started_at)
            remaining_pct = 100 - self._last_progress_value
            eta_s = int(remaining_pct / max(0.001, rate))
            eta_txt = self._format_hms(max(0, eta_s))
        elif self._last_progress_value >= 100:
            eta_txt = "00:00:00"

        self._timing_label.setText(f"Elapsed: {elapsed_txt} | ETA: {eta_txt}")

    @staticmethod
    def _format_hms(total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def show_cancel_button(self, show: bool) -> None:
        """Show or hide the cancel button."""
        self._cancel_button.setVisible(show)

    def connect_cancel(self, callback) -> None:
        """Connect cancel button to a callback."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                self._cancel_button.clicked.disconnect()
            except Exception:
                pass
        self._cancel_button.clicked.connect(callback)
