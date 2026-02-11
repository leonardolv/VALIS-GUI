"""Tests for ValisWorker and thread management."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore

from valis_workstation.models.config import Config
from valis_workstation.workers.valis_worker import ValisWorker


class TestValisWorkerSignals:
    def test_emits_finished_on_success(self, qtbot, monkeypatch, tmp_path: Path) -> None:
        def fake_pipeline(config, slides, output_dir, progress_callback=None, cancel_check=None):
            if progress_callback:
                progress_callback(50)
                progress_callback(100)
            return {"output_dir": str(output_dir), "registered_dir": str(output_dir)}

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            fake_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.finished, timeout=3000) as blocker:
            thread.start()

        thread.quit()
        thread.wait()
        assert blocker.args[0]["output_dir"] == str(tmp_path)

    def test_emits_failed_on_exception(self, qtbot, monkeypatch, tmp_path: Path) -> None:
        def failing_pipeline(*args, **kwargs):
            raise RuntimeError("Pipeline exploded")

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            failing_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.failed, timeout=3000) as blocker:
            thread.start()

        thread.quit()
        thread.wait()
        assert "exploded" in blocker.args[0].lower()

    def test_cancel_sets_flag(self) -> None:
        worker = ValisWorker(Config(), [], Path("."))
        assert worker._cancel_requested is False
        worker.cancel()
        assert worker._cancel_requested is True

    def test_emits_cancelled_when_flag_set(self, qtbot, monkeypatch, tmp_path: Path) -> None:
        def cancelling_pipeline(config, slides, output_dir, progress_callback=None, cancel_check=None):
            return {"output_dir": str(output_dir)}

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            cancelling_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        worker._cancel_requested = True  # pre-set cancel

        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.cancelled, timeout=3000):
            thread.start()

        thread.quit()
        thread.wait()
