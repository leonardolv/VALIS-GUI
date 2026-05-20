from __future__ import annotations

import logging
import re
import time

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.ui.icons import load_icon
from valis_workstation.utils.qt_logging import QtLogEmitter

logger = logging.getLogger(__name__)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


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
        self._progress.setFormat("%p%")

        self._stage_label = QtWidgets.QLabel("Stage: Idle")
        self._stage_label.setToolTip("Current pipeline stage")
        self._timing_label = QtWidgets.QLabel("Elapsed: 00:00:00 | ETA: --:--:--")
        self._timing_label.setProperty("role", "sidebar-subtle")
        self._timing_label.setToolTip("Elapsed time since run started and estimated time remaining")
        self._run_started_at: float | None = None
        self._last_progress_value = 0

        self._timing_timer = QtCore.QTimer(self)
        self._timing_timer.setInterval(1000)
        self._timing_timer.timeout.connect(self._update_timing)
        self._timing_timer.start()

        self._log_header = QtWidgets.QLabel("Log Output")
        self._log_header.setProperty("role", "sidebar-header")

        filter_row = QtWidgets.QHBoxLayout()
        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setPlaceholderText("Filter log lines...")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.setToolTip("Filter log lines by keyword (case-insensitive)")
        self._filter_edit.textChanged.connect(self._rebuild_log_view)
        filter_row.addWidget(self._filter_edit)

        log_controls = QtWidgets.QHBoxLayout()
        self._auto_scroll_check = QtWidgets.QCheckBox("Auto-scroll")
        self._auto_scroll_check.setChecked(True)
        self._auto_scroll_check.setToolTip(
            "Automatically scroll the log to show new lines as they arrive"
        )

        self._clear_log_button = QtWidgets.QPushButton("Clear Log")
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
        self._log_console.setAccessibleName("Registration log")
        self._log_console.document().setMaximumBlockCount(2000)
        self._log_console.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._log_console.customContextMenuRequested.connect(self._show_log_context_menu)
        self._log_lines: list[str] = []

        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        divider.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

        layout.addWidget(self._stage_label)
        layout.addWidget(self._progress)
        layout.addWidget(self._timing_label)
        layout.addWidget(self._cancel_button)
        layout.addWidget(divider)
        layout.addWidget(self._log_header)
        layout.addLayout(filter_row)
        layout.addLayout(log_controls)
        layout.addWidget(self._log_console)
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

    def _clear_log(self) -> None:
        if len(self._log_lines) > 0:
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

    def _copy_log(self) -> None:
        text = "\n".join(self._log_lines)
        QtWidgets.QApplication.clipboard().setText(text)
        if hasattr(self, "window") and callable(self.window):
            self.window().statusBar().showMessage("Log copied to clipboard", 3000)

    def _save_log_as(self) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        last_dir = settings.value("ui/last_log_save_dir", str(__import__('pathlib').Path.home()))

        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Log",
            last_dir + "/registration_log.txt",
            "Text Files (*.txt)",
        )
        if not out_path:
            return
        try:
            settings.setValue("ui/last_log_save_dir", str(__import__('pathlib').Path(out_path).parent))
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(self._log_lines))
            if hasattr(self, "window") and callable(self.window):
                self.window().statusBar().showMessage(f"Log saved to {out_path}", 4000)
        except Exception as exc:
            logger.exception("Failed to save log output: %s", exc)

    def set_stage(self, stage: str) -> None:
        self._stage_label.setText(f"Stage: {stage}")
        if stage.lower() in {"starting", "preparing pipeline"}:
            self._run_started_at = time.time()

    def set_progress(self, value: int) -> None:
        value = max(0, min(100, value))
        self._last_progress_value = value
        self._progress.setValue(value)
        if value >= 100:
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
        try:
            self._cancel_button.clicked.disconnect()
        except Exception:
            pass
        self._cancel_button.clicked.connect(callback)
