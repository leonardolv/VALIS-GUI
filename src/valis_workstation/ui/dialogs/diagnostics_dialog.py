from __future__ import annotations

import platform
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets


class DiagnosticsDialog(QtWidgets.QDialog):
    """Display environment and runtime diagnostics."""

    def __init__(
        self,
        repo_root: Path,
        last_result: dict | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)

        self._text = QtWidgets.QPlainTextEdit()
        self._text.setReadOnly(True)
        layout.addWidget(self._text)

        btn_row = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        self._refresh_btn.clicked.connect(
            lambda: self._populate(repo_root, last_result)
        )
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch(1)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._populate(repo_root, last_result)

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
