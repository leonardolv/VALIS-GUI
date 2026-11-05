"""Tests for PerformanceStatsDialog accessibility, tooltips, and headless cache clearance."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore
from valis_workstation.ui.dialogs.performance_stats_dialog import (
    PerformanceStatsDialog,
)


def test_performance_stats_dialog_accessibility_and_tooltips(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Object names and dialog accessibility
    assert dialog.objectName() == "performanceStatsDialog"
    assert dialog.accessibleName() == "Performance Statistics Dialog"
    assert dialog._tabs.objectName() == "performanceTabs"
    assert dialog._tabs.accessibleName() == "Performance Statistics Categories"

    # Accessible names
    assert dialog._refresh_btn.accessibleName() == "Refresh Performance Statistics"
    assert dialog._clear_thumb_cache_btn.accessibleName() == "Clear Thumbnail Cache"
    assert dialog._close_btn.accessibleName() == "Close Dialog"
    assert dialog._thumb_cache_bar.accessibleName() == "Thumbnail Cache Usage"

    # Object names
    assert dialog._refresh_btn.objectName() == "perfRefreshBtn"
    assert dialog._clear_thumb_cache_btn.objectName() == "perfClearCacheBtn"
    assert dialog._close_btn.objectName() == "perfCloseBtn"
    assert dialog._thumb_cache_bar.objectName() == "perfThumbCacheBar"

    # Tooltips
    assert "refresh" in dialog._refresh_btn.toolTip().lower()
    assert "thumbnail" in dialog._clear_thumb_cache_btn.toolTip().lower()
    assert "close" in dialog._close_btn.toolTip().lower()

    # Cursors
    assert dialog._refresh_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._clear_thumb_cache_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_performance_stats_dialog_refresh_action(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Click refresh
    dialog._refresh_btn.click()
    assert dialog._update_timer.isActive()


def test_performance_stats_dialog_clear_cache_headless(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Click clear thumbnail cache in headless mode without blocking
    dialog._clear_thumb_cache_btn.click()
    assert dialog._thumb_total_label.text() is not None


def test_refresh_timer_stops_on_accept_and_reject(qtbot):
    """Close button/Escape use accept()/reject(), which skip closeEvent."""
    for finish in ("accept", "reject"):
        dialog = PerformanceStatsDialog()
        qtbot.addWidget(dialog)
        assert dialog._update_timer.isActive()
        getattr(dialog, finish)()
        assert not dialog._update_timer.isActive()


def test_performance_stats_dialog_properties_and_query_helpers(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Property accessors
    assert dialog.tabs == dialog._tabs
    assert dialog.refresh_button == dialog._refresh_btn
    assert dialog.clear_cache_button == dialog._clear_thumb_cache_btn
    assert dialog.close_button == dialog._close_btn
    assert dialog.thumb_cache_bar == dialog._thumb_cache_bar

    # Metric query helpers
    assert dialog.is_auto_refresh_active() is True
    assert dialog.tab_count() == 3
    assert dialog.current_tab_title() == "Overview"
    assert isinstance(dialog.uptime_text(), str)
    assert isinstance(dialog.current_memory_text(), str)
    assert isinstance(dialog.peak_memory_text(), str)
    assert isinstance(dialog.thumb_hit_rate_text(), str)
    assert isinstance(dialog.slides_loaded_count(), int)
    assert isinstance(dialog.registration_runs_count(), int)
    assert isinstance(dialog.cached_thumbnails_count(), int)

    # Tab switching reflected in query helper
    dialog.tabs.setCurrentIndex(1)
    assert dialog.current_tab_title() == "Thumbnail Cache"
    dialog.tabs.setCurrentIndex(2)
    assert dialog.current_tab_title() == "Memory"

    dialog.accept()
    assert dialog.is_auto_refresh_active() is False

