import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

if importlib.util.find_spec("pytestqt") is None:
    pytest.skip("pytest-qt not available", allow_module_level=True)

from PySide6 import QtCore

from valis_workstation.models.config import Config
from valis_workstation.workers.valis_worker import ValisWorker


def test_worker_emits_finished(qtbot, monkeypatch, tmp_path: Path) -> None:
    def fake_pipeline(config, slides, output_dir, progress_callback=None):
        if progress_callback:
            progress_callback(100)
        return {"output_dir": output_dir}

    monkeypatch.setattr(
        "valis_workstation.services.valis_pipeline.run_valis_pipeline", fake_pipeline
    )

    config = Config()
    slides = [tmp_path / "slide.tif"]
    slides[0].write_text("data")

    thread = QtCore.QThread()
    worker = ValisWorker(config, slides, tmp_path)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)

    with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
        thread.start()

    thread.quit()
    thread.wait()

    assert blocker.args[0]["output_dir"] == tmp_path
