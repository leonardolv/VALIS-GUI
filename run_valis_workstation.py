#!/usr/bin/env python3
"""Entry point for running VALIS Workstation from a repo checkout."""
from __future__ import annotations

import sys
import importlib
import importlib.util
from pathlib import Path


def _ensure_src_on_path(repo_root: Path) -> None:
    src_path = repo_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _ensure_logs_dir(repo_root: Path) -> Path:
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _configure_qt_defaults() -> None:
    if importlib.util.find_spec("PySide6") is None:
        return
    QtCore = importlib.import_module("PySide6.QtCore")
    QtCore.QCoreApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    _ensure_src_on_path(repo_root)
    _ensure_logs_dir(repo_root)
    _configure_qt_defaults()

    from valis_workstation.__main__ import main as app_main

    return app_main()


if __name__ == "__main__":
    raise SystemExit(main())
