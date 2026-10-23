"""Tests for ThumbnailCache (disk-based cache)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication

from valis_workstation.services.thumbnail_cache import ThumbnailCache


@pytest.fixture()
def _ensure_qapp():
    """Ensure a QApplication exists for QPixmap operations."""
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture()
def cache(tmp_path: Path, _ensure_qapp):
    return ThumbnailCache(cache_dir=tmp_path / "cache", max_cache_size_mb=10)


@pytest.fixture()
def dummy_slide(tmp_path: Path) -> Path:
    slide = tmp_path / "slide.tif"
    slide.write_bytes(b"\x00" * 100)
    return slide


def _make_pixmap(w: int = 64, h: int = 64) -> QPixmap:
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(0xFF0000)
    return QPixmap.fromImage(img)


class TestThumbnailCache:
    def test_miss_on_empty(self, cache, dummy_slide) -> None:
        result = cache.get(dummy_slide)
        assert result is None

    def test_put_and_get(self, cache, dummy_slide) -> None:
        px = _make_pixmap()
        metadata = {"width": 64, "height": 64}
        ok = cache.put(dummy_slide, px, metadata)
        assert ok

        result = cache.get(dummy_slide)
        assert result is not None
        pixmap, meta = result
        assert not pixmap.isNull()
        assert meta["width"] == 64

    def test_invalidation_on_mtime_change(self, cache, dummy_slide) -> None:
        px = _make_pixmap()
        cache.put(dummy_slide, px, {})

        # Simulate file modification by rewriting
        import os, time

        time.sleep(0.1)
        dummy_slide.write_bytes(b"\xff" * 200)
        # Force mtime difference > 1s
        os.utime(dummy_slide, (time.time() + 10, time.time() + 10))

        result = cache.get(dummy_slide)
        assert result is None

    def test_missing_slide_returns_none(self, cache, tmp_path) -> None:
        result = cache.get(tmp_path / "nonexistent.tif")
        assert result is None

    def test_clear(self, cache, dummy_slide) -> None:
        cache.put(dummy_slide, _make_pixmap(), {})
        cache.clear()
        result = cache.get(dummy_slide)
        assert result is None

    def test_stats(self, cache, dummy_slide) -> None:
        cache.put(dummy_slide, _make_pixmap(), {})
        stats = cache.get_stats()
        assert stats["count"] == 1
        assert stats["size_mb"] > 0


class TestEviction:
    def _fill(self, cache, n: int, png_bytes: int, json_bytes: int) -> list[Path]:
        import os

        cache.cache_dir.mkdir(parents=True, exist_ok=True)
        pngs = []
        for i in range(n):
            png = cache.cache_dir / f"k{i}.png"
            png.write_bytes(b"x" * png_bytes)
            png.with_suffix(".json").write_bytes(b"y" * json_bytes)
            os.utime(png, (1000 + i, 1000 + i))
            pngs.append(png)
        return pngs

    def test_eviction_counts_metadata_and_stops_at_target(self, cache) -> None:
        # 10 entries of 0.5MB png + 0.5MB json = 1MB each, limit 10MB: sits at
        # the limit, so add one more to go over and evict down to 9MB.
        mb = 1024 * 1024
        cache.max_cache_size_mb = 10
        pngs = self._fill(cache, 11, mb // 2, mb // 2)
        cache._check_cache_size()
        remaining = [p for p in pngs if p.exists()]
        # 11MB -> must drop to <= 9MB: exactly 2 oldest evicted, not more.
        assert len(remaining) == 9
        assert not pngs[0].exists() and not pngs[1].exists()
        assert not pngs[0].with_suffix(".json").exists()

    def test_vanished_file_does_not_abort_cleanup(self, cache, monkeypatch) -> None:
        mb = 1024 * 1024
        cache.max_cache_size_mb = 1
        pngs = self._fill(cache, 5, mb // 2, 0)
        real_stat = Path.stat

        def flaky(self, *a, **k):
            if self.name == "k1.png":
                raise FileNotFoundError(self)
            return real_stat(self, *a, **k)

        monkeypatch.setattr(Path, "stat", flaky)
        cache._check_cache_size()
        monkeypatch.undo()
        assert sum(p.exists() for p in pngs) < 5

    def test_clear_tolerates_subdirectory(self, cache, dummy_slide) -> None:
        cache.put(dummy_slide, _make_pixmap(), {})
        (cache.cache_dir / "subdir").mkdir()
        cache.clear()
        assert cache.get_stats()["count"] == 0
