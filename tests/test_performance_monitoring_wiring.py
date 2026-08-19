"""``PerformanceMonitor.track_*`` had no caller anywhere in the app.

Backlog: "``PerformanceMonitor.track_thumbnail_load``/``track_tile_load``/etc.
have no caller anywhere in the app." ``PerformanceStatsDialog`` reads
``monitor.metrics.thumbnail_cache_hits`` / ``.thumbnail_load_times`` / etc.
and displays them, but nothing that actually loads a thumbnail, loads a
slide, or runs a registration ever called the tracker that would populate
those fields — so the dialog's numbers were always zero, regardless of the
"Enable performance monitoring" checkbox (``performance/monitoring_enabled``,
also unread anywhere until now).

Three real call sites are wired:

* ``generate_thumbnail`` (``services/thumbnail_generator.py``) times itself
  and calls ``track_thumbnail_load`` on both a cache hit and a fresh
  generation.
* ``MainWindow._load_thumbnails_parallel`` calls ``track_slides_loaded`` once
  the whole folder's worth of thumbnails has been generated — it already
  computed ``started_at``/elapsed time for the loading overlay's ETA, so the
  duration was sitting right there unused.
* ``ValisWorker.run`` times the ``run_valis_pipeline`` call and calls
  ``track_registration`` right before emitting ``finished``.

``TileCache`` (``utils/tile_cache.py``) is a separate, deeper gap: nothing in
the app outside its own module and the stats dialog ever calls
``get_tile_cache()`` at all, so there is no real tile-loading call site to
wire ``track_tile_load`` into yet (filed back to the Backlog rather than
folded in here) — that tab's numbers already come from the cache's own
internal hit/miss counters (``TileCache.get_stats()``), not from
``PerformanceMonitor``, so it was not actually broken the way the thumbnail
and registration numbers were.

All tracking is gated by ``performance/monitoring_enabled`` (default
``True``), read fresh on every call the same way the app's existing
``ui/show_tooltips`` filter re-reads its own setting — a Preferences change
takes effect immediately, no restart needed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from valis_workstation.utils import performance as perf_module
from valis_workstation.utils.performance import (
    PerformanceMonitor,
    _monitoring_enabled,
    get_performance_monitor,
)


@pytest.fixture(autouse=True)
def _clean_monitoring_setting():
    settings = QtCore.QSettings("VALIS", "Workstation")
    previous = settings.value("performance/monitoring_enabled", None)
    yield
    if previous is None:
        settings.remove("performance/monitoring_enabled")
    else:
        settings.setValue("performance/monitoring_enabled", previous)


@pytest.fixture(autouse=True)
def _reset_global_monitor():
    """``get_performance_monitor()`` is a process-wide singleton.

    Every real call site fetches it fresh, so a test that wants to assert on
    ``.metrics`` needs a monitor nothing else has already written to.
    """
    perf_module._global_monitor = None
    yield
    perf_module._global_monitor = None


# ---------------------------------------------------------------------------
# performance/monitoring_enabled -> _monitoring_enabled()
# ---------------------------------------------------------------------------


class TestMonitoringEnabledSetting:
    def test_defaults_to_enabled_when_unset(self):
        QtCore.QSettings("VALIS", "Workstation").remove(
            "performance/monitoring_enabled"
        )
        assert _monitoring_enabled() is True

    def test_respects_false(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", False
        )
        assert _monitoring_enabled() is False

    def test_respects_true(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        assert _monitoring_enabled() is True


# ---------------------------------------------------------------------------
# The tracker methods themselves honor the setting
# ---------------------------------------------------------------------------


class TestTrackersRespectTheToggle:
    def test_thumbnail_load_is_recorded_when_enabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        monitor = PerformanceMonitor()
        monitor.track_thumbnail_load(0.01, from_cache=True)
        assert monitor.metrics.thumbnail_cache_hits == 1
        assert monitor.metrics.thumbnail_load_times == [0.01]

    def test_thumbnail_load_is_a_no_op_when_disabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", False
        )
        monitor = PerformanceMonitor()
        monitor.track_thumbnail_load(0.01, from_cache=True)
        assert monitor.metrics.thumbnail_cache_hits == 0
        assert monitor.metrics.thumbnail_load_times == []

    def test_registration_is_a_no_op_when_disabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", False
        )
        monitor = PerformanceMonitor()
        monitor.track_registration(1.5)
        assert monitor.metrics.registration_times == []

    def test_slides_loaded_is_a_no_op_when_disabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", False
        )
        monitor = PerformanceMonitor()
        monitor.track_slides_loaded(5, 2.0)
        assert monitor.metrics.slide_count == 0

    def test_slides_loaded_tolerates_a_zero_count(self):
        """The lone real caller only calls this when it loaded >=1 slide, but
        the method's own average-per-slide log line divides by ``count`` —
        guard the case directly rather than relying on the caller forever."""
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        monitor = PerformanceMonitor()
        monitor.track_slides_loaded(0, 0.0)  # must not raise
        assert monitor.metrics.slide_count == 0

    def test_memory_peak_and_samples_are_not_recorded_when_disabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", False
        )
        monitor = PerformanceMonitor()
        current = monitor.sample_memory()
        assert current > 0, "the live reading itself should still work"
        assert monitor.metrics.memory_samples == []
        assert monitor.metrics.peak_memory_mb == 0.0

    def test_memory_peak_and_samples_are_recorded_when_enabled(self):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        monitor = PerformanceMonitor()
        monitor.sample_memory()
        assert len(monitor.metrics.memory_samples) == 1
        assert monitor.metrics.peak_memory_mb > 0.0


# ---------------------------------------------------------------------------
# generate_thumbnail -> track_thumbnail_load
# ---------------------------------------------------------------------------


class TestThumbnailGeneratorWiring:
    def test_a_cache_hit_is_tracked(self, tmp_path, monkeypatch):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        slide_path = tmp_path / "slide.svs"
        slide_path.write_bytes(b"not a real slide")

        from valis_workstation.services import thumbnail_generator as gen_module

        fake_cache = MagicMock()
        fake_cache.get.return_value = (MagicMock(name="pixmap"), {"cached": True})
        monkeypatch.setattr(
            gen_module, "get_thumbnail_cache", lambda: fake_cache
        )

        result = gen_module.generate_thumbnail(slide_path)

        assert result == fake_cache.get.return_value
        monitor = get_performance_monitor()
        assert monitor.metrics.thumbnail_cache_hits == 1
        assert monitor.metrics.thumbnail_cache_misses == 0
        assert len(monitor.metrics.thumbnail_load_times) == 1

    def test_a_missing_file_is_not_tracked(self, tmp_path):
        from valis_workstation.services import thumbnail_generator as gen_module

        gen_module.generate_thumbnail(tmp_path / "does_not_exist.svs")

        monitor = get_performance_monitor()
        assert monitor.metrics.thumbnail_load_times == []


# ---------------------------------------------------------------------------
# ValisWorker.run -> track_registration
# ---------------------------------------------------------------------------


class TestValisWorkerTracksRegistration:
    def test_a_successful_run_is_tracked(self, qtbot, monkeypatch, tmp_path: Path):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        from valis_workstation.models.config import Config
        from valis_workstation.workers.valis_worker import ValisWorker

        def fake_pipeline(config, slides, output_dir, progress_callback=None, cancel_check=None):
            return {"output_dir": str(output_dir)}

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            fake_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.finished, timeout=3000):
            thread.start()
        thread.quit()
        thread.wait()

        monitor = get_performance_monitor()
        assert len(monitor.metrics.registration_times) == 1
        assert monitor.metrics.registration_times[0] >= 0

    def test_a_failed_run_is_not_tracked(self, qtbot, monkeypatch, tmp_path: Path):
        from valis_workstation.models.config import Config
        from valis_workstation.workers.valis_worker import ValisWorker

        def failing_pipeline(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            failing_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.failed, timeout=3000):
            thread.start()
        thread.quit()
        thread.wait()

        monitor = get_performance_monitor()
        assert monitor.metrics.registration_times == []


# ---------------------------------------------------------------------------
# MainWindow._load_thumbnails_parallel -> track_slides_loaded
# ---------------------------------------------------------------------------


class TestLoadThumbnailsParallelTracksSlideLoads:
    @pytest.fixture()
    def win(self, qtbot, monkeypatch, tmp_path):
        _original_find_spec = importlib.util.find_spec

        def _patched_find_spec(name, *args, **kwargs):
            if name == "napari":
                return None
            return _original_find_spec(name, *args, **kwargs)

        monkeypatch.setattr(importlib.util, "find_spec", _patched_find_spec)
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "question",
            staticmethod(
                lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Yes
            ),
        )

        from valis_workstation.main_window import MainWindow
        from valis_workstation.utils.qt_logging import QtLogEmitter

        w = MainWindow(
            repo_root=tmp_path,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        return w

    def test_a_folder_load_is_tracked(self, win, monkeypatch, tmp_path):
        QtCore.QSettings("VALIS", "Workstation").setValue(
            "performance/monitoring_enabled", True
        )
        slides = [tmp_path / "a.svs", tmp_path / "b.svs"]
        for s in slides:
            s.write_bytes(b"x")

        with patch(
            "valis_workstation.services.thumbnail_generator.generate_thumbnail",
            return_value=(None, {}),
        ):
            win._load_thumbnails_parallel(slides, overlay=None)

        monitor = get_performance_monitor()
        assert monitor.metrics.slide_count == 2
        assert monitor.metrics.total_slide_load_time >= 0
