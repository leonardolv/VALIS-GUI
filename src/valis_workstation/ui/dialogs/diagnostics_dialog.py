from __future__ import annotations

import platform
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets


class DiagnosticsDialog(QtWidgets.QDialog):
    """Display environment and runtime diagnostics."""

    _COPY_LABEL = "Copy to Clipboard"

    def __init__(
        self,
        repo_root: Path,
        last_result: dict | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("diagnosticsDialog")
        self.setAccessibleName("Diagnostics Dialog")
        self.setWindowTitle("Diagnostics")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)

        self._text = QtWidgets.QPlainTextEdit()
        self._text.setObjectName("diagnosticsText")
        self._text.setReadOnly(True)
        self._text.setAccessibleName("Diagnostics Output")
        self._text.setToolTip("System environment and runtime diagnostics log")
        layout.addWidget(self._text)

        btn_row = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        self._refresh_btn.setObjectName("diagnosticsRefreshBtn")
        self._refresh_btn.setAccessibleName("Refresh Diagnostics")
        self._refresh_btn.setToolTip("Reload system and workstation runtime diagnostics")
        self._refresh_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(
            lambda: self._populate(repo_root, last_result)
        )
        btn_row.addWidget(self._refresh_btn)

        self._copy_btn = QtWidgets.QPushButton(self._COPY_LABEL)
        self._copy_btn.setObjectName("diagnosticsCopyBtn")
        self._copy_btn.setAccessibleName("Copy Diagnostics to Clipboard")
        self._copy_btn.setToolTip("Copy complete diagnostics report to system clipboard")
        self._copy_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(self._copy_btn)

        btn_row.addStretch(1)

        self._close_btn = QtWidgets.QPushButton("Close")
        self._close_btn.setObjectName("diagnosticsCloseBtn")
        self._close_btn.setAccessibleName("Close Diagnostics")
        self._close_btn.setToolTip("Close the diagnostics dialog")
        self._close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._close_btn)
        layout.addLayout(btn_row)

        self._populate(repo_root, last_result)

    def _copy_to_clipboard(self) -> None:
        """Copy the diagnostic text to the clipboard and provide visual feedback."""
        text = self._text.toPlainText()
        QtWidgets.QApplication.clipboard().setText(text)
        # Restore the label captured at construction, never the current text:
        # a second click inside the feedback window would otherwise capture
        # "Copied!" itself and leave the button stuck on it.
        self._copy_btn.setText("✓ Copied!")

        def _reset() -> None:
            try:
                self._copy_btn.setText(self._COPY_LABEL)
            except RuntimeError:
                pass

        QtCore.QTimer.singleShot(2000, self, _reset)

    def _populate(self, repo_root: Path, last_result: dict | None) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        recent = settings.value("recent_folders", [])
        if not isinstance(recent, list):
            recent = []

        lines = [
            "VALIS Workstation Diagnostics",
            "=" * 32,
            f"Python: {sys.version.split()[0]}",
            f"Platform: {platform.platform()}",
            f"Qt: {QtCore.qVersion()}",
            f"Repo root: {repo_root}",
            f"Recent folders: {len(recent)}",
        ]

        if last_result:
            lines.append("")
            lines.append("Last registration result:")
            for key in ("output_dir", "registered_dir"):
                if key in last_result:
                    lines.append(f"  - {key}: {last_result[key]}")

        log_file = repo_root / "logs" / "valis_workstation.log"
        lines.append(f"Log file exists: {log_file.exists()} ({log_file})")

        self._text.setPlainText("\n".join(lines))
