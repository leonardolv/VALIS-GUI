"""Tests for utility modules: paths, exceptions, performance."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from valis_workstation.utils.paths import ensure_dir, normalize_path
from valis_workstation.utils.exceptions import UserVisibleError, ValisWorkstationError
from valis_workstation.utils.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    TimingContext,
)


# ---------- paths ----------
class TestPaths:
    def test_ensure_dir_creates(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        result = ensure_dir(target)
        assert target.exists()
        assert result == target

    def test_ensure_dir_idempotent(self, tmp_path: Path) -> None:
        target = tmp_path / "d"
        ensure_dir(target)
        ensure_dir(target)  # second call should not error
        assert target.exists()

    def test_normalize_path(self) -> None:
        p = normalize_path(".")
        assert p.is_absolute()


# ---------- exceptions ----------
class TestExceptions:
    def test_base_is_exception(self) -> None:
        assert issubclass(ValisWorkstationError, Exception)

    def test_user_visible_inherits(self) -> None:
        assert issubclass(UserVisibleError, ValisWorkstationError)

    def test_raise_and_catch(self) -> None:
        with pytest.raises(UserVisibleError, match="oops"):
            raise UserVisibleError("oops")


# ---------- PerformanceMetrics ----------
class TestPerformanceMetrics:
    def test_empty_summary(self) -> None:
        m = PerformanceMetrics()
        s = m.get_summary()
        assert s["thumbnails"]["total_generated"] == 0
        assert s["tiles"]["cache_hit_rate"] == 0
        assert s["registration"]["total_runs"] == 0
        assert s["memory"]["peak_mb"] == 0.0
        assert s["slides"]["count"] == 0

    def test_cache_hit_rate(self) -> None:
        m = PerformanceMetrics(thumbnail_cache_hits=3, thumbnail_cache_misses=7)
        s = m.get_summary()
        assert abs(s["thumbnails"]["cache_hit_rate"] - 0.3) < 1e-9


# ---------- PerformanceMonitor ----------
class TestPerformanceMonitor:
    def test_track_thumbnail(self) -> None:
        mon = PerformanceMonitor()
        mon.track_thumbnail_load(0.05, from_cache=False)
        mon.track_thumbnail_load(0.01, from_cache=True)
        assert mon.metrics.thumbnail_cache_hits == 1
        assert mon.metrics.thumbnail_cache_misses == 1
        assert len(mon.metrics.thumbnail_load_times) == 2

    def test_track_tile(self) -> None:
        mon = PerformanceMonitor()
        mon.track_tile_load(0.02, from_cache=True)
        assert mon.metrics.tile_cache_hits == 1

    def test_track_registration(self) -> None:
        mon = PerformanceMonitor()
        mon.track_registration(10.5)
        assert mon.metrics.registration_times == [10.5]

    def test_track_slides(self) -> None:
        mon = PerformanceMonitor()
        mon.track_slides_loaded(5, 2.5)
        assert mon.metrics.slide_count == 5
        assert mon.metrics.total_slide_load_time == 2.5

    def test_sample_memory(self) -> None:
        mon = PerformanceMonitor()
        mem = mon.sample_memory()
        assert mem > 0

    def test_summary_includes_uptime(self) -> None:
        mon = PerformanceMonitor()
        s = mon.get_summary()
        assert "uptime_s" in s

    def test_status_message(self) -> None:
        mon = PerformanceMonitor()
        msg = mon.get_status_message()
        assert "Mem" in msg


# ---------- TimingContext ----------
class TestTimingContext:
    def test_timing_captures_duration(self) -> None:
        with TimingContext("test_op", log_result=False) as t:
            time.sleep(0.01)
        assert t.duration >= 0.005

    def test_timing_on_exception(self) -> None:
        with pytest.raises(ValueError):
            with TimingContext("fail_op", log_result=False) as t:
                raise ValueError("boom")
        assert t.duration >= 0
